import os
import logging

import json
import paramiko
import tarfile
import shutil
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
        "_".join(["cluster", str(cluster_id)]),
        settings.CHEF_NODES_DATABAG_NAME
    )

    nodes = Node.objects.filter(cluster__id=cluster_id)
    if not nodes:
        raise Exception("Nodes list is empty")

    for node in nodes:
        node_json = {}
        node_solo = {
            "cluster_id": cluster_id,
            "run_list": []
        }

        roles_for_node = node.roles.all()
        if not roles_for_node:
            raise Exception("Roles list for node %s is empty" % node.id)

        node_json['cluster_id'] = cluster_id
        for f in node._meta.fields:
            if f.name != 'cluster':
                node_json[f.name] = getattr(node, f.name)

        node_json['roles'] = []
        for role in roles_for_node:
            rc = [r.recipe for r in role.recipes.all()]
            node_solo["run_list"].extend(rc)
            node_json["roles"].append({
                "name": role.name,
                "recipes": rc
            })

        if not os.path.exists(databag):
            os.makedirs(databag)

        # writing to solo
        with open(
            os.path.join(
                settings.CHEF_CONF_FOLDER,
                "".join([node.id, ".json"])
            ),
            "w"
        ) as entity:
            entity.write(json.dumps(node_solo))

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
