import os
import json
from django.conf import settings
from celery.task import task
from nailgun.models import Environment, Node, Role


@task
def create_chef_config(environment_id):
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
                [x.name for x in r.nodes.filter(environment__id=env_id)]

    solo_json = {}
    # Extend solo_json for each node by specifying role
    #    assignment for this particular node
    for n in nodes:
        solo_json['run_list'] = \
                ["role[" + x.name + "]" for x in n.roles.all()]
        solo_json['all_roles'] = nodes_per_role

        filepath = os.path.join(settings.CHEF_CONF_FOLDER,
                n.name + '.json')
        f = open(filepath, 'w')
        f.write(json.dumps(solo_json))
        f.close()

    return True
