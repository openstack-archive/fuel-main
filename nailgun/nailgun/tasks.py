import os
import logging

import json
import paramiko
from django.conf import settings
from celery.task import task
from celery.task import subtask
from celery.task import group

from nailgun.models import Cluster, Node, Role
from nailgun.helpers import SshConnect

logger = logging.getLogger(__name__)


@task
def deploy_cluster(cluster_id):
    databag = os.path.join(
        settings.CHEF_CONF_FOLDER,
        settings.CHEF_NODES_DATABAG_NAME
    )

    nodes = Node.objects.filter(cluster__id=cluster_id)
    if not nodes:
        raise Exception("Nodes list is empty")

    for node in nodes:
        node_json = {}

        roles_for_node = node.roles.all()
        if not roles_for_node:
            raise Exception("Roles list for node %s is empty" % node.id)

        for f in node._meta.fields:
            if f.name == 'cluster':
                node_json['cluster_id'] = node.cluster_id
            else:
                node_json[f.name] = getattr(node, f.name)

        node_json['roles'] = []
        for role in roles_for_node:
            node_json['roles'].append({
                "name": role.name,
                "recipes": [r.recipe for r in role.recipes.all()]
            })

        if not os.path.exists(databag):
            os.mkdir(databag)

        with open(
            os.path.join(databag, "".join([node.id, ".json"])),
            "w"
        ) as entity:
            entity.write(json.dumps(node_json))

    job = group(subtask(bootstrap_node, args=(n.id, )) for n in nodes)
    result = job.apply_async()
    return result


@task
def bootstrap_node(node_id):
    _provision_node(node_id)

    node = Node.objects.get(id__exact=node_id)
    try:
        ssh = SshConnect(node.ip, 'root', settings.PATH_TO_SSH_KEY)
        # Returns True if succeeded
        exit_status = ssh.run("/opt/nailgun/bin/deploy")
    except (paramiko.AuthenticationException,
            paramiko.PasswordRequiredException,
            paramiko.SSHException):
        logger.exception("Can't connect to %s, ip=%s", node.id, node.ip)
        return {node.id: False}
    except Exception:
        logger.exception("Error in deployment of %s, ip=%s", node.id, node.ip)
        return {node.id: False}
    #finally:
        #ssh.close()
    return {node.id: exit_status}


# Call to Cobbler to make node ready.
def _provision_node(node_id):
    pass
