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
import pprint

from nailgun import models
from nailgun import settings

from nailgun.exceptions import EmptyListError, NotFound


logger = logging.getLogger("helpers")


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


class EndPointDataDriver:
    def __init__(self, node):
        self.node = node

    def node_ip(self, network_name):
        for ip_addr in models.IPAddr.objects.filter(node__id=self.node.id):
            network = models.Network.objects.get(id=ip_addr.network.id)
            if network.name == network_name:
                return ip_addr.ip_addr

    def node_netmask(self, network_name):
        release = self.node.cluster.release
        network = models.Network.objects.get(name=network_name,
                                             release=release)
        return network.netmask

    def node_vlan(self, network_name):
        release = self.node.cluster.release
        network = models.Network.objects.get(name=network_name,
                                             release=release)
        return network.vlan_id


class EndPointManager:
    def __init__(self, data_driver, name, scheme):

        self.data_driver = data_driver
        self.name = name
        self.scheme = scheme
        self.data = {}

    def generator_ip_repo(self, args):
        return settings.REPO_ADDRESS

    def generator_ip(self, network_name):
        network_name = str(network_name)
        ip = self.data_driver.node_ip(network_name)
        logger.debug("EndPointManager: generator_ip: %s" % ip)
        return ip

    def generator_netmask(self, network_name):
        network_name = str(network_name)
        netmask = self.data_driver.node_netmask(network_name)
        logger.debug("EndPointManager: generator_netmask: %s" % netmask)
        return netmask

    def generator_vlan(self, network_name):
        network_name = str(network_name)
        vlan_id = self.data_driver.node_vlan(network_name)
        logger.debug("EndPointManager: generator_vlan: %s" % vlan_id)
        return vlan_id

    def generator_url(self, url_args):
        url_args = dict(url_args)
        ip = self.data_driver.node_ip(url_args['network'])
        url = "%s://%s:%s%s" % (url_args['protocol'],
                                ip,
                                url_args['port'],
                                url_args.get('url', ''))
        logger.debug("EndPointManager: generator_url: %s" % url)
        return url

    def generator_transparent(self, args):
        logger.debug("EndPointManager: generator_transparent: %s" % \
                         args)
        return args

    def generator_password(self, length=8):
        length = int(length)
        password = ''.join(
            choice(
                ''.join((string.ascii_letters, string.digits))
                ) for _ in xrange(length)
            )
        logger.debug("EndPointManager: generator_password: %s" % \
                         password)
        return password

    @classmethod
    def merge_dictionary(cls, dst, src):
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

    @classmethod
    def list2dict(cls, d, k):
        """
        Creating a nested dictionary:
        ['a', 'b', 'c', 'd'] => {'a': {'b': {'c': 'd'}}}
        Merging it with the main dict updates the single key
        """
        _d = copy.deepcopy(d)
        if len(k) > 1:
            _k = k.pop(0)
            _d[_k] = cls.list2dict(d, k)
            return _d
        return k.pop(0)

    def instantiate(self):
        for k in self.scheme:
            logger.debug("EndPointManager: generating %s" % k)
            generator = getattr(self, self.scheme[k]["generator"])
            generator_args = self.scheme[k]["generator_args"]
            generated = generator(generator_args)

            attributes = self.scheme[k]["attribute"]
            """
            example of attribute:
            ["service.mysql.user", "service.postgresql.user"]
            """
            if not isinstance(attributes, (list, tuple)):
                attributes = [attributes]

            for attribute in attributes:
                attribute_keys = re.split(ur'\.', attribute)
                logger.debug("EndPointManager: attribute_keys: %s" % \
                                 str(attribute_keys))

                attribute_keys.append(generated)
                logger.debug("EndPointManager: attribute_keys: %s" % \
                                 str(attribute_keys))
                attribute_dict = self.list2dict({}, attribute_keys)
                logger.debug("EndPointManager: attribute_dict: %s" % \
                                 str(attribute_dict))

                self.merge_dictionary(self.data, attribute_dict)

    def get_data(self):
        logger.debug("EndPointManager: data: %s" % \
                         str(self.data))
        return self.data


class DeployManager:
    def __init__(self, cluster_id):
        self.cluster_id = cluster_id
        self.cluster_component_ids = [
            c.id for n, r, c in self._cluster_iterator()
            ]
        self.release_id = models.Cluster.objects.get(id=cluster_id).release.id

    def sorted_components(self):
        graph = {}
        for component in models.Com.objects.filter(
            id__in=self.cluster_component_ids
            ):
            self._resolve_cluster_deps(graph, component)

        try:
            sorted_components = self._topol_sort(graph)
        except KeyError:
            raise Exception("Cluster dependencies cannot be resolved")

        logger.debug("sorted_components: %s" % \
                         pprint.pformat(sorted_components))
        return sorted_components

    def _cluster_iterator(self):
        for node in models.Node.objects.filter(cluster__id=self.cluster_id):
            for role in node.roles.all():
                for component in role.components.all():
                    yield [node, role, component]

    def _resolve_cluster_deps(self, graph, component):
        if component.name not in graph:
            graph[component.name] = []
            requires = component.requires.all()
            logger.debug("Resolving cluster: component %s requires: %s" % \
                             (component.name,
                              str([p.name for p in requires])))

            for provided_by in models.Com.objects.filter(
                id__in=self.cluster_component_ids,
                provides__in=requires
                ):
                graph[component.name].append(provided_by.name)
                self._resolve_cluster_deps(graph, provided_by)

    def _topol_sort(self, graph):
        """ Depth First Traversal algorithm for sorting DAG graph.

        Example graph: 1 depends on 4; 3 depends on 2 and 6; etc.
        Example code:

        .. code-block:: python

        >>> graph = {1: [4], 2: [], 3: [2,6], 4:[2,3], 5: [], 6: [2]}
        >>> topol_sort(graph)
        [2, 6, 3, 4, 1, 5]

        Exception is raised if there is a cycle:

        .. code-block:: python

        >>> graph = {1: [4], 2: [], 3: [2,6], 4:[2,3,1], 5: [], 6: [2]}
        >>> topol_sort(graph)
        ...
        Exception: Graph contains cycles, processed 4 depends on 1

        """

        def dfs(v):
            color[v] = "gray"
            for w in graph[v]:
                if color[w] == "black":
                    continue
                elif color[w] == "gray":
                    raise Exception(
                        "Graph contains cycles, processed %s depends on %s" % \
                            (v, w))
                dfs(w)
            color[v] = "black"
            _sorted.append(v)

        _sorted = []
        color = {}
        for j in graph:
            color[j] = "white"
        for i in graph:
            if color[i] == "white":
                dfs(i)

        return _sorted

    def clean_cluster(self):
        models.EndPoint.objects.filter(
            node__in=models.Node.objects.filter(cluster__id=self.cluster_id)
            ).delete()

    def instantiate_cluster(self):

        for node in models.Node.objects.filter(cluster__id=self.cluster_id):

            """
            it is needed to be checked if node have only one component
            assignment of given component and only one given point
            """
            components_used = []
            points_used = []

            data_driver = EndPointDataDriver(node)

            roles = node.roles.all()
            for role in roles:
                components = role.components.all()
                for component in components:
                    if component.name in components_used:
                        raise Exception(
                            "Duplicated component: node: %s com: %s" % \
                                (node.id, component.name))
                    components_used.append(component.name)

                    provides = list(component.provides.all())

                    logger.debug("Com %s provides %s" % \
                                     (component.name,
                                      str([p.name for p in provides])))

                    for point in provides:
                        if point.name in points_used:
                            raise Exception(
                                "Duplicated point: node: %s point: %s" % \
                                    (node.id, point.name))
                        points_used.append(point.name)

                        logger.debug("Instantiating point: %s" % point.name)
                        manager = EndPointManager(
                            data_driver,
                            point.name,
                            point.scheme
                            )
                        manager.instantiate()

                        end_point = models.EndPoint(
                            point=point,
                            node=node,
                            data=manager.get_data()
                            )

                        end_point.save()


class DeployDriver:
    def __init__(self, node, component):
        self.node = node
        self.component = component

    @classmethod
    def merge_dictionary(cls, dst, src):
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

    def endpoint_iterator(self, node, component):
        logger.debug("endpoint_iterator: node: %s component: %s" % \
                         (node.id, component.name))
        for point in component.provides.all():
            logger.debug("endpoint_iterator: component: %s provides: %s" % \
                             (component.name, point.name))
            try:
                logger.debug("endpoint_iterator: looking for provided "\
                                 "endpoint point: %s node: %s" % \
                                 (point.name, node.id))
                ep = models.EndPoint.objects.get(point=point, node=node)
            except ObjectDoesNotExist as e:
                logger.debug("endpoint_iterator: provided endpoint "\
                                 "is not found point: %s node: %s" % \
                                 (point.name, node.id))
                raise Exception("Provided point %s instance is not found" % \
                                    point.name)
            except Exception as e:
                logger.debug("Exception: %s" % str(e))
                raise e
            else:
                logger.debug("endpoint_iterator: provided endpoint found " \
                                 "point: %s node: %s endpoint: %s" % \
                                 (point.name, node.id, ep.id))
                yield ep

        for point in component.requires.all():
            """
            FOR THE START WE TRY TO FIND ENDPOINT INSTANCE
            BOUND TO THIS NODE. IT IT FAILS THEN WE LOOK FOR
            ENDPOINT INSTANCES BOUND TO OTHER NODES IN CLUSTER
            """
            try:
                ep = models.EndPoint.objects.get(
                    point=point,
                    node=node
                    )
            except:
                pass
            else:
                yield ep

            eps = models.EndPoint.objects.filter(point=point)

            if eps:
                """
                FIXME
                WE NEED MORE INTELLIGENT ALGORITHM TO CHOOSE
                WHICH ENDPOINT INSTANCE IS A MOST SUITABLE
                ONE FOR THIS COMPONENT. AT THE MOMENT WE
                SIMPLY RETURN FIRST FOUND INSTANCE
                """
                ep = eps[0]
                logger.debug("endpoint_iterator: required endpoint found " \
                                 "point: %s node: %s" % \
                                 (point.name, ep.node.id))

                yield ep
            else:
                raise Exception("Required point %s instance is not found" % \
                                    point.name)

    def deploy_data(self):
        self.data = {}
        try:
            for endpoint in self.endpoint_iterator(self.node, self.component):
                logger.error("Found endpoint id: %s for n=%s c=%s" % \
                                 (endpoint.id, self.node.id,
                                  self.component.name))
                self.merge_dictionary(self.data, endpoint.data)
        except:
            logger.error("Error while getting endpoints for n=%s c=%s" % \
                             (self.node.id, self.component.name))
            raise Exception("Getting endpoints failed: node=%s com=%s" % \
                                (self.node.id, self.component.name))

        logger.debug("Node: %s com: %s data: %s" % \
                         (self.node.id, self.component.name, str(self.data)))
        return {
            "chef-solo": self.chef_solo_data,
            "puppet": self.puppet_data,
            }[self.component.deploy["driver"]]()

    def chef_solo_data(self):
        chef_data = {
            "run_list": self.component.deploy["driver_args"]["run_list"]
            }
        if self.component.deploy["driver_args"].get("cooks", None) is not None:
            chef_data["cooks"] = \
                self.component.deploy["driver_args"]["cooks"]
        logger.debug("Chef-data: %s" % str(chef_data))
        self.merge_dictionary(chef_data, self.data)
        return chef_data

    def puppet_data(self):
        return self.data
