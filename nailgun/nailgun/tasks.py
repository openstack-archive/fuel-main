import os
import logging

import json
import paramiko
from django.conf import settings
from celery.task import task
from celery.task import subtask
from celery.task import group

from nailgun.models import Environment, Node, Role
from nailgun.helpers import SshConnect


logger = logging.getLogger(__name__)


@task
def deploy_env(environment_id):
    create_chef_config.delay(environment_id, callback=run_chef_solo)
    # TODO(mihgen): return info about subtasks
    return True


@task
def create_chef_config(environment_id, callback=None):
    env_id = environment_id
    nodes = Node.objects.filter(environment__id=env_id)
    roles = Role.objects.all()
    if not (nodes and roles):
        raise Exception("Roles or Nodes list is empty")

    nodes_per_role = {}
    # For each role in the system
    for r in roles:
        # Find nodes that have this role. Filter nodes by env_id
        nodes_per_role[r.name] = \
                [x.name for x in r.node_set.filter(environment__id=env_id)]

    solo_json = {}
    # Extend solo_json for each node by specifying role
    #    assignment for this particular node
    for n in nodes:
        solo_json['run_list'] = \
                ["role[" + x.name + "]" for x in n.roles.all()]
        solo_json['all_roles'] = nodes_per_role

        filepath = os.path.join(settings.CHEF_CONF_FOLDER,
                n.id + '.json')
        f = open(filepath, 'w')
        f.write(json.dumps(solo_json))
        f.close()

    if callback:
        job = group(subtask(callback, args=(n.ip, )) for n in nodes)
        result = job.apply_async()
        return True
    return True


@task
def run_chef_solo(host):
    try:
        ssh = SshConnect(host, 'root', settings.PATH_TO_SSH_KEY)
        # Returns True if succeeded
        ssh.run("id")
    except (paramiko.AuthenticationException,
            paramiko.PasswordRequiredException,
            paramiko.SSHException):
        logger.exception("Can't connect to host %s.", host)
        return False   # TODO(mihgen): set status FAILURE ?
    except Exception:
        logger.exception("Error in deployment of %s.", host)
        return False   # TODO(mihgen): set status FAILURE ?
    #finally:
        #ssh.close()

    return True
