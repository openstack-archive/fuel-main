import logging
import socket
import paramiko
import copy
import string
import logging
from random import choice
import re
import time
import socket

from nailgun.models import Node, Recipe, IPAddr, Network
from nailgun.exceptions import EmptyListError, NotFound


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


def merge_dictionary(dst, src):
    """
    'True' way of merging two dictionaries
    (python dict.update() updates just top-level keys and items)
    """
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) \
                    and isinstance(current_dst[key], dict):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst


def generate_passwords(d):
    stack = []
    new_dict = d.copy()

    def create_pass():
        return ''.join(
            choice(
                string.printable.replace('"', '').replace('\\', '')
            ) for _ in xrange(10)
        )

    def construct(d, k):
        """
        Creating a nested dictionary:
        ['a', 'b', 'c', 'd'] => {'a': {'b': {'c': 'd'}}}
        Merging it with the main dict updates the single key
        """
        _d = copy.deepcopy(d)
        if len(k) > 1:
            _k = k.pop(0)
            _d[_k] = construct(d, k)
            return _d
        return k.pop(0)

    def search_pwd(node, cdict):
        """
        Recursively searching for 'password' fields
        """
        for a, val in node.items():
            stack.append(a)
            if isinstance(val, dict):
                search_pwd(val, cdict)
            elif "password" in a:
                k = stack[:]
                k.append(create_pass())
                c = construct({}, k)
                cdict = merge_dictionary(cdict, c)
            stack.pop()
        return cdict

    search_pwd(d, new_dict)
    return new_dict


class DeployGenerator:
    @classmethod
    def components4(cls, cluster_id, method="list"):

        if method == "list":
            attrs = []
        else:
            attrs = {}

        nodes = Node.objects.filter(cluster__id=cluster_id)
        for node in nodes:

            node_attrs = cls.node_attrs(node.id)

            if isinstance(attrs, (list,)):
                node_attrs["node_id"] = node.id
                attrs.append(node_attrs)
            else:
                attrs[node.id] = node_attrs

        return attrs

    @classmethod
    def node_attrs(self, node_id, force=False):
        node = Node.objects.get(id=node_id)
        if force or not node.node_attrs:

            node_ips = {}
            ip_addrs = IPAddr.objects.filter(node__id=node.id)
            for ip_addr in ip_addrs:
                network = Network.objects.get(id=ip_addr.network.id)
                node_ips[network.name] = ip_addr.ip_addr

            node_attrs = {
                "node_ips": node_ips
                }

            roles = node.roles.all()
            for role in roles:
                recipes = role.recipes.all()
                for recipe in recipes:
                    if recipe.attribute:
                        node_attrs = merge_dictionary(
                            node_attrs,
                            recipe.attribute.attribute
                            )
                        node_attrs = generate_passwords(node_attrs)
            node.node_attrs = node_attrs
            node.save()
        return Node.objects.get(id=node_id).node_attrs

    @classmethod
    def recipes(cls, cluster_id):
        used_recipes = []
        nodes = Node.objects.filter(cluster__id=cluster_id)
        if not nodes:
            raise EmptyListError("Node list is empty")

        for node in nodes:
            roles = node.roles.all()
            for role in roles:
                recipes = role.recipes.all()
                for recipe in recipes:
                    used_recipes.append(recipe.recipe)

        return used_recipes


class DatabagGenerator:
    def __init__(self, cluster_id):
        self.cluster_id = cluster_id
        self.node_jsons = {}
        self.use_recipes = []

    def generate(self):
        nodes = Node.objects.filter(cluster__id=self.cluster_id)
        if not nodes:
            raise EmptyListError("Node list is empty")

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
                    self.use_recipes.append(r.recipe)
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

            self.node_jsons[node.id] = node_json
