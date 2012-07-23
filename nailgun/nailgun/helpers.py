import logging
import socket
import paramiko
from nailgun.models import Node
from nailgun.exceptions import EmptyListError


logger = logging.getLogger(__name__)


class SshConnect(object):

    def __init__(self, host, user, keyfile=None, password=None):
        try:
            self.host = host
            self.t = paramiko.Transport((host, 22))
            if password:
                self.t.connect(username=user, password=password)
            elif keyfile:
                self.t.connect(username=user,
                    pkey=paramiko.RSAKey.from_private_key_file(keyfile))

        except:
            self.close()
            raise

    def run(self, cmd, timeout=30):
        logger.debug("[%s] Running command: %s", self.host, cmd)
        chan = self.t.open_session()
        chan.settimeout(timeout)
        chan.exec_command(cmd)
        return chan.recv_exit_status() == 0

    def close(self):
        try:
            if self.t:
                self.t.close()
        except:
            pass


class DatabagGenerator:
    def __init__(self, cluster_id):
        self.cluster_id = cluster_id

    def generate(self):
        node_jsons = {}
        
        nodes = Node.objects.filter(cluster__id=self.cluster_id)
        if not nodes:
            raise EmptyListError("Node list is empty")

        use_recipes = []
        for node in nodes:
            node_json = {}
            add_attrs = {}

            roles_for_node = node.roles.all()

            node_json['cluster_id'] = self.cluster_id
            for f in node._meta.fields:
                if f.name != 'cluster':
                    node_json[f.name] = getattr(node, f.name)

            node_json['roles'] = []
            for role in roles_for_node:
                recipes = role.recipes.all()
                rc = []
                for r in recipes:
                    rc.append("recipe[%s]" % r.recipe)
                    use_recipes.append(r.recipe)
                    if r.attribute:
                        add_attrs = merge_dictionary(
                            add_attrs,
                            r.attribute.attribute
                            )
                        add_attrs = generate_passwords(add_attrs)

                node_json["roles"].append({
                        "name": role.name,
                        "recipes": rc
                        })

            node_json = merge_dictionary(node_json, add_attrs)

            if 'network' in node.metadata:
                node_json['network'] = node.metadata['network']

            node_jsons[node.id] = node_json

        return node_jsons

