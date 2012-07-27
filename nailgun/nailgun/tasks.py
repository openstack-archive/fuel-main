import os
import os.path
import copy
import string
import logging
from random import choice
import re
import time
import socket

import json
import paramiko
import tarfile
import shutil
from django.conf import settings

from nailgun.models import Cluster, Node, Role, Recipe
from nailgun.helpers import SshConnect, DeployGenerator
from nailgun.task_helpers import task_with_callbacks, TaskPool, topol_sort
from nailgun.exceptions import SSHError, EmptyListError, DeployError
from nailgun.provision import ProvisionConfig
from nailgun.provision import ProvisionFactory
from nailgun.provision.model.profile import Profile as ProvisionProfile
from nailgun.provision.model.node import Node as ProvisionNode
from nailgun.provision.model.power import Power as ProvisionPower

from celery import current_app
from celery.utils import LOG_LEVELS
from celery.log import Logging


current_app.conf.CELERYD_LOG_LEVEL = LOG_LEVELS[settings.CELERYLOGLEVEL]
celery_logging = Logging(current_app)
celery_logging.setup_logger(logfile=settings.CELERYLOGFILE)
logger = celery_logging.get_default_logger()


def resolve_recipe_deps(graph, recipe):
    if recipe.recipe not in graph:
        graph[recipe.recipe] = []
    for r in recipe.depends.all():
        graph[recipe.recipe].append(r.recipe)
        resolve_recipe_deps(graph, r)


@task_with_callbacks
def update_cluster_status(*args):
    # FIXME(mihgen):
    # We have to do this ugly trick because chord precedes first argument
    if isinstance(args[0], list):
        args = args[1:]
    cluster_id = args[0]

    return cluster_id


def node_set_error_status(node_id):
    node = Node.objects.get(id=node_id)
    node.status = "error"
    node.save()

@task_with_callbacks(name='Deploy Cluster')
def deploy_cluster(cluster_id):

    graph = {}
    for recipe in Recipe.objects.filter(
        recipe__in=DeployGenerator.recipes(cluster_id)
        ):
        resolve_recipe_deps(graph, recipe)
        #graph[recipe.recipe] = [r.recipe for r in recipe.depends.all()]

    # NOTE(mihgen): Installation components dependency resolution
    # From nodes.roles.recipes we know recipes that needs to be applied
    # We have to apply them in an order according to specified dependencies
    # To sort in an order, we use DFS(Depth First Traversal) over DAG graph
    sorted_recipes = topol_sort(graph)
    tree = TaskPool()
    # first element in sorted_recipes is the first recipe we have to apply
    installed = []
    for r in sorted_recipes:
        recipe = Recipe.objects.get(recipe=r)
        # We need to find nodes with these recipes
        roles = recipe.roles.all()
        nodes = Node.objects.filter(roles__in=roles, cluster__id=cluster_id)

        # TODO(mihgen): What if there are no nodes with required role?
        #   we need to raise an exception if there are any roles dependend

        taskset = []
        for node in nodes:
            bootstrap_args = [node.id]
            if node.id in installed:
                bootstrap_args.append(True)
            else:
                installed.append(node.id)
            taskset.append({'func': bootstrap_node, 'args': bootstrap_args,
                    'kwargs': {}})
        tree.push_task(create_solo, (cluster_id, recipe.id))
        # FIXME(mihgen): it there are no taskset items,
        #   we included recipes which are not applied on nodes.
        #   We have to include only recipes which are assigned to nodes
        if taskset:
            tree.push_task(taskset)

    tree.push_task(update_cluster_status, (cluster_id,))
    res = tree.apply_async()
    return res


@task_with_callbacks
def create_solo(*args):
    logger = create_solo.get_logger()
    # FIXME(mihgen):
    # We have to do this ugly trick because chord precedes first argument
    if isinstance(args[0], list):
        args = args[1:]
    cluster_id, recipe = args[0], Recipe.objects.get(id=args[1])

    # We need to find nodes with these recipes
    roles = recipe.roles.all()
    nodes = Node.objects.filter(roles__in=roles)

    for node in nodes:
        node_solo = {
            "cluster_id": cluster_id,
            "run_list": ["recipe[%s]" % recipe.recipe],
            "components_list": DeployGenerator.components4(cluster_id),
            "components_dict": DeployGenerator.components4(cluster_id, "dict")
        }

        # writing to solo
        with open(
            os.path.join(
                settings.CHEF_CONF_FOLDER,
                "".join([node.id, ".json"])
            ),
            "w"
        ) as entity:
            entity.write(json.dumps(node_solo, sort_keys=True, indent=4))

    return True


def tcp_ping(host, port):
    s = socket.socket()
    try:
        s.connect((str(host), int(port)))
    except socket.error:
        return False
    s.close()
    return True


@task_with_callbacks
def bootstrap_node(node_id, installed=False):

    node = Node.objects.get(id=node_id)
    logger.debug("Turning node %s status into 'deploying'" % node_id)
    node.status = "deploying"
    node.save()

    if not installed:
        logger.debug("Provisioning node %s" % node_id)
        _provision_node(node_id)
    else:
        logger.debug("Provisioning skipped - node %s \
            is already installed" % node_id)

    # FIXME
    # node.ip had been got from bootstrap agent
    # there is no guarantee that installed slave node has
    # the same ip as bootstrap node had
    # it is necessary to install and launch agent on slave node

    logger.debug("Waiting for node %s listen to %s:%s ..." \
                     % (node_id, str(node.ip), "22"))
    while True:
        if tcp_ping(node.ip, 22):
            break
        time.sleep(5)

    logger.debug("Trying to connect to node %s over ssh" % node_id)
    try:
        ssh = SshConnect(node.ip, 'root', settings.PATH_TO_SSH_KEY)
    except (paramiko.AuthenticationException,
            paramiko.PasswordRequiredException,
            paramiko.SSHException):
        logger.error("Error occured while ssh connecting to node %s" % node_id)
        message = "Task %s failed:" \
            "Can't connect to IP=%s" \
            % (bootstrap_node.request.id, node.ip)
        node_set_error_status(node.id)
        raise SSHError(message)
    except Exception, error:
        message = "Task %s failed:" \
            "Error during ssh/deploy IP=%s: %s" \
            % (bootstrap_node.request.id, node.ip, str(error))
        node_set_error_status(node.id)
        raise SSHError(message)
    else:
        logger.debug("Trying to launch deploy script on node %s" % node_id)
        # Returns True if succeeded
        exit_status = ssh.run("/opt/nailgun/bin/deploy")
        ssh.close()

    # ssh.run returns True, if command executed successfully
    # FIXME(mihgen): rename it/refactor, it's unclear
    if not exit_status:
        logger.error("Error occured while deploying node %s" % node_id)
        message = "Task %s failed: " \
            "Deployment exited with non-zero exit code. IP=%s" \
            % (bootstrap_node.request.id, node.ip)
        node_set_error_status(node.id)
        raise DeployError(message)

    logger.debug("Turning node %s status into 'ready'" % node_id)
    node.status = "ready"
    node.save()
    return exit_status


def _is_node_libvirt(node):
    rex = re.compile(ur"^QEMU Virtual CPU", re.I)
    if rex.match(node.metadata["cpu"]["0"]["model_name"]):
        return True
    return Falsedefault - 134132450898


def _is_node_bootstrap(node):
    logger.debug(
        "Checking if node %s is booted with bootstrap image" \
        % node.id
    )
    try:
        logger.debug(
            "Trying to establish ssh connection using bootstrap key"
        )
        ssh = SshConnect(
            node.ip,
            'root',
            settings.PATH_TO_BOOTSTRAP_SSH_KEY
        )
    except (paramiko.AuthenticationException,
            paramiko.PasswordRequiredException):
        logger.debug("Auth error while ssh using bootstrap rsa key")
        return False
    except Exception:
        logger.debug("Unknown error while ssh using bootstrap rsa key")
        return False
    else:
        ssh.close()
        return True


# Call to Cobbler to make node ready.
def _provision_node(node_id):
    node = Node.objects.get(id=node_id)

    pc = ProvisionConfig()
    pc.cn = "nailgun.provision.driver.cobbler.Cobbler"
    pc.url = settings.COBBLER_URL
    pc.user = settings.COBBLER_USER
    pc.password = settings.COBBLER_PASSWORD

    pd = ProvisionFactory.getInstance(pc)

    pf = ProvisionProfile(settings.COBBLER_PROFILE)

    ndp = ProvisionPower("ssh")
    ndp.power_user = "root"

    if _is_node_bootstrap(node):
        logger.info("Node %s seems booted with bootstrap image" % node_id)
        ndp.power_pass = "rsa:%s" % settings.PATH_TO_BOOTSTRAP_SSH_KEY
    else:
        logger.info("Node %s seems booted with real system" % node_id)
        ndp.power_pass = "rsa:%s" % settings.PATH_TO_SSH_KEY
    ndp.power_address = node.ip

    nd = ProvisionNode(node_id)
    nd.driver = pd
    nd.mac = node.mac
    nd.profile = pf
    nd.pxe = True
    nd.kopts = ""
    nd.power = ndp

    logger.debug(
        "Trying to save node %s into provision system" \
        % node_id
    )
    nd.save()

    logger.debug(
        "Trying to reboot node %s using %s" \
        % (node_id, ndp.power_type)
    )
    nd.power_reboot()
