import os
import logging

import json
import paramiko
import tarfile
import shutil
from django.conf import settings

from nailgun.models import Cluster, Node, Role, Recipe
from nailgun.helpers import SshConnect
from nailgun.task_helpers import task_with_callbacks, TaskPool, topol_sort

logger = logging.getLogger(__name__)


class TaskError(Exception):

    def __init__(self, task_id, error, cluster_id=None, node_id=None):
        self.message = ""
        node_msg = ""
        cluster_msg = ""

        if node_id:
            node_msg = ", node_id='%s'" % (node_id)
        if cluster_id:
            cluster_msg = ", cluster_id='%s'" % (cluster_id)

        self.message = "Error in task='%s'%s%s. Error message: '%s'" % (
                    task_id, cluster_msg, node_msg, error)

        try:
            Exception.__init__(self, self.message)
            logger.error(self.message)
            if node_id:
                node = Node.objects.get(id=node_id)
                node.status = "error"
                node.save()
        except:
            logger.exception("Exception in exception handler occured")

    def __str__(self):
        return repr(self.message)


@task_with_callbacks
def deploy_cluster(cluster_id):
    databag = os.path.join(
        settings.CHEF_CONF_FOLDER,
        "_".join(["cluster", str(cluster_id)]),
        settings.CHEF_NODES_DATABAG_NAME
    )

    nodes = Node.objects.filter(cluster__id=cluster_id)
    if not nodes:
        raise TaskError(deploy_cluster.request.id,
                "Nodes list is empty.", cluster_id=cluster_id)

    use_recipes = []
    for node in nodes:
        node_json = {}

        roles_for_node = node.roles.all()
        # TODO(mihgen): It should be possible to have node w/o role assigned
        if not roles_for_node:
            raise TaskError(deploy_cluster.request.id,
                    "Roles list for node %s is empty" % node.id,
                    cluster_id=cluster_id)

        node_json['cluster_id'] = cluster_id
        for f in node._meta.fields:
            if f.name != 'cluster':
                node_json[f.name] = getattr(node, f.name)

        node_json['roles'] = []
        for role in roles_for_node:
            rc = ["recipe[%s]" % r.recipe for r in role.recipes.all()]
            use_recipes.extend(rc)
            node_json["roles"].append({
                "name": role.name,
                "recipes": rc
            })

        if not os.path.exists(databag):
            os.makedirs(databag)

        # writing to databag
        with open(
            os.path.join(databag, "".join([node.id, ".json"])),
            "w"
        ) as entity:
            entity.write(json.dumps(node_json))

    t = tarfile.open("".join([databag, ".tar.gz"]), "w:gz")
    t.add(databag, os.path.basename(databag))
    t.close()
    # removing databag - it's already packed
    shutil.rmtree(databag)

    graph = {}
    # FIXME(mihgen):!!!!! all_recipes only for our cluster_id !!!!!!!
    all_recipes = Recipe.objects.all()
    for recipe in all_recipes:
        graph[recipe] = []

    sorted_recipes = topol_sort(graph)
    tree = TaskPool()
    # first element in sorted_recipes is the first recipe we have to apply
    for recipe in sorted_recipes:
        # We need to find nodes with these recipes
        roles = recipe.roles.all()
        nodes = Node.objects.filter(roles__in=roles)

        # TODO(mihgen): What if there are no nodes with required role?
        #   we need to raise an exception if there are any roles dependend

        taskset = []
        for node in nodes:
            taskset.append({'func': bootstrap_node, 'args': (node.id,),
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
def update_cluster_status(*args):
    # FIXME(mihgen):
    # We have to do this ugly trick because chord precedes first argument
    if isinstance(args[0], list):
        args = args[1:]
    cluster_id = args[0]

    # TODO(mihgen): update status of cluster deployment as done
    return cluster_id


@task_with_callbacks
def create_solo(*args):
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
            "run_list": recipe.recipe
        }

        # writing to solo
        with open(
            os.path.join(
                settings.CHEF_CONF_FOLDER,
                "".join([node.id, ".json"])
            ),
            "w"
        ) as entity:
            entity.write(json.dumps(node_solo))

    return True


@task_with_callbacks
def bootstrap_node(node_id):
    node = Node.objects.get(id=node_id)
    node.status = "deploying"
    node.save()

    _provision_node(node_id)

    try:
        ssh = SshConnect(node.ip, 'root', settings.PATH_TO_SSH_KEY)
        # Returns True if succeeded
        exit_status = ssh.run("/opt/nailgun/bin/deploy")
    except (paramiko.AuthenticationException,
            paramiko.PasswordRequiredException,
            paramiko.SSHException):
        raise TaskError(bootstrap_node.request.id,
                "Can't connect to IP=%s" % node.ip, node_id=node.id)
    except Exception:
        raise TaskError(bootstrap_node.request.id,
                "Unknown error during ssh/deploy IP=%s" % node.ip,
                node_id=node.id)
    # FIXME(mihgen): If uncomment, it fails in case if SshConnect.__init__
    #                failed. But we need to close ssh in other cases
    #finally:
        #ssh.close()
    #ssh.close()
    if not exit_status:
        raise TaskError(bootstrap_node.request.id,
                "Deployment exited with non-zero exit code. IP=%s" % node.ip,
                node_id=node.id)
    node.status = "ready"
    node.save()
    return exit_status


# Call to Cobbler to make node ready.
def _provision_node(node_id):
    pass
