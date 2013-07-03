# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid
import itertools
import traceback
import subprocess
import shlex
import json

import web
import netaddr
from sqlalchemy.orm import object_mapper, ColumnProperty
from sqlalchemy import or_

import nailgun.rpc as rpc
from nailgun.db import db
from nailgun.logger import logger
from nailgun.settings import settings
from nailgun import notifier
from nailgun.network.manager import NetworkManager
from nailgun.api.models import Base
from nailgun.api.models import Network
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.api.models import Cluster
from nailgun.api.models import IPAddr
from nailgun.api.models import Release
from nailgun.task.fake import FAKE_THREADS
from nailgun.errors import errors
from nailgun.task.helpers import TaskHelper


def fake_cast(queue, messages, **kwargs):
    def make_thread(message, join_to=None):
        thread = FAKE_THREADS[message['method']](
            data=message,
            params=kwargs,
            join_to=join_to
        )
        logger.debug("Fake thread called: data: %s, params: %s",
                     message, kwargs)
        thread.start()
        thread.name = message['method'].upper()
        return thread

    if isinstance(messages, (list,)):
        thread = None
        for m in messages:
            thread = make_thread(m, join_to=thread)
    else:
        make_thread(messages)


if settings.FAKE_TASKS or settings.FAKE_TASKS_AMQP:
    rpc.cast = fake_cast


class DeploymentTask(object):
# LOGIC
# Use cases:
# 1. Cluster exists, node(s) added
#   If we add one node to existing OpenStack cluster, other nodes may require
#   updates (redeployment), but they don't require full system reinstallation.
#   How to: run deployment for all nodes which system type is target.
#   Run provisioning first and then deployment for nodes which are in
#   discover system type.
#   Q: Should we care about node status (provisioning, error, deploying)?
#   A: offline - when node doesn't respond (agent doesn't run, not
#                implemented); let's say user should remove this node from
#                cluster before deployment.
#      ready - target OS is loaded and node is Ok, we redeploy
#              ready nodes only if cluster has pending changes i.e.
#              network or cluster attrs were changed
#      discover - in discovery mode, provisioning is required
#      provisioning - at the time of task execution there should not be such
#                     case. If there is - previous provisioning has failed.
#                     Possible solution would be to try again to provision
#      deploying - the same as provisioning, but stucked in previous deploy,
#                  solution - try to deploy. May loose some data if reprovis.
#      error - recognized error in deployment or provisioning... We have to
#              know where the error was. If in deployment - reprovisioning may
#              not be a solution (can loose data). If in provisioning - can do
#              provisioning & deployment again
# 2. New cluster, just added nodes
#   Provision first, and run deploy as second
# 3. Remove some and add some another node
#   Deletion task will run first and will actually remove nodes, include
#   removal from DB.. however removal from DB happens when remove_nodes_resp
#   is ran. It means we have to filter nodes and not to run deployment on
#   those which are prepared for removal.

    @classmethod
    def message(cls, task):
        logger.debug("DeploymentTask.message(task=%s)" % task.uuid)
        task_uuid = task.uuid
        cluster_id = task.cluster.id
        netmanager = NetworkManager()

        nodes = TaskHelper.nodes_to_deploy(task.cluster)

        logger.info("Associated FQDNs to nodes: %s" %
                    ', '.join([n.fqdn for n in nodes]))

        nodes_ids = [n.id for n in nodes]
        if nodes_ids:
            logger.info("Assigning IP addresses to nodes..")
            netmanager.assign_ips(nodes_ids, "management")
            netmanager.assign_ips(nodes_ids, "public")
            netmanager.assign_ips(nodes_ids, "storage")

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            if n.status in ('ready', 'deploying'):
                n.status = 'provisioned'
            n.progress = 0
            db().add(n)
            db().commit()
            nodes_with_attrs.append(cls.__format_node_for_naily(n))

        cluster_attrs = task.cluster.attributes.merged_attrs_values()
        cluster_attrs['controller_nodes'] = cls.__controller_nodes(cluster_id)

        nets_db = db().query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).all()

        ng_db = db().query(NetworkGroup).filter_by(
            cluster_id=cluster_id).all()
        for net in ng_db:
            net_name = net.name + '_network_range'
            if net.name == 'floating':
                cluster_attrs[net_name] = \
                    cls.__get_ip_addresses_in_ranges(net)
            elif net.name == 'public':
                # We shouldn't pass public_network_range attribute
                continue
            else:
                cluster_attrs[net_name] = net.cidr

        cluster_attrs['network_manager'] = task.cluster.net_manager

        fixed_net = db().query(NetworkGroup).filter_by(
            cluster_id=cluster_id).filter_by(name='fixed').first()
        # network_size is required for all managers, otherwise
        #  puppet will use default (255)
        cluster_attrs['network_size'] = fixed_net.network_size
        if cluster_attrs['network_manager'] == 'VlanManager':
            cluster_attrs['num_networks'] = fixed_net.amount
            cluster_attrs['vlan_start'] = fixed_net.vlan_start
            cls.__add_vlan_interfaces(nodes_with_attrs)

        if task.cluster.mode == 'ha':
            logger.info("HA mode chosen, creating VIP addresses for it..")
            cluster_attrs['management_vip'] = netmanager.assign_vip(
                cluster_id, "management")
            cluster_attrs['public_vip'] = netmanager.assign_vip(
                cluster_id, "public")

        cluster_attrs['deployment_mode'] = task.cluster.mode
        cluster_attrs['deployment_id'] = cluster_id

        message = {
            'method': 'deploy',
            'respond_to': 'deploy_resp',
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes_with_attrs,
                'attributes': cluster_attrs
            }
        }

        return message

    @classmethod
    def execute(cls, task):
        logger.debug("DeploymentTask.execute(task=%s)" % task.uuid)
        message = cls.message(task)
        task.cache = message
        db().add(task)
        db().commit()
        rpc.cast('naily', message)

    @classmethod
    def __format_node_for_naily(cls, n):
        netmanager = NetworkManager()
        return {
            'id': n.id, 'status': n.status, 'error_type': n.error_type,
            'uid': n.id, 'ip': n.ip, 'mac': n.mac, 'role': n.role,
            'fqdn': n.fqdn, 'progress': n.progress, 'meta': n.meta,
            'network_data': netmanager.get_node_networks(n.id),
            'online': n.online
        }

    @classmethod
    def __add_vlan_interfaces(cls, nodes):
        """
        We shouldn't pass to orchetrator fixed network
        when network manager is VlanManager, but we should specify
        fixed_interface (private_interface in terms of fuel) as result
        we just pass vlan_interface as node attribute.
        """
        netmanager = NetworkManager()
        for node in nodes:
            node_db = db().query(Node).get(node['id'])

            fixed_interface = netmanager._get_interface_by_network_name(
                node_db.id, 'fixed')

            node['vlan_interface'] = fixed_interface.name

    @classmethod
    def __controller_nodes(cls, cluster_id):
        nodes = db().query(Node).filter_by(
            cluster_id=cluster_id,
            role='controller',
            pending_deletion=False).order_by(Node.id)

        return map(cls.__format_node_for_naily, nodes)

    @classmethod
    def __get_ip_addresses_in_ranges(cls, network_group):
        """
        Get array of all possibale ip addresses in all ranges
        """
        ranges = []
        for ip_range in network_group.ip_ranges:
            ranges += map(lambda ip: str(ip),
                          list(netaddr.IPRange(ip_range.first, ip_range.last)))

        # Return only uniq ip addresses
        return sorted(list(set(ranges)))


class ProvisionTask(object):
    @classmethod
    def message(cls, task):
        logger.debug("ProvisionTask.message(task=%s)" % task.uuid)
        # this variable is used to set 'auth_key' in cobbler ks_meta
        cluster_attrs = task.cluster.attributes.merged_attrs_values()
        nodes = TaskHelper.nodes_to_provision(task.cluster)
        netmanager = NetworkManager()

        USE_FAKE = settings.FAKE_TASKS or settings.FAKE_TASKS_AMQP
        # TODO: For now we send nodes data to orchestrator
        # which is cobbler oriented. But for future we
        # need to use more abstract data structure.
        nodes_data = []
        for node in nodes:
            if not node.online:
                if not USE_FAKE:
                    raise errors.NodeOffline(
                        u"Node '%s' (id=%s) is offline."
                        " Remove it from environment and try again." %
                        (node.name, node.id)
                    )
                else:
                    logger.warning(
                        u"Node '%s' (id=%s) is offline."
                        " Remove it from environment and try again." %
                        (node.name, node.id)
                    )

            cobbler_profile = cluster_attrs['cobbler']['profile']

            node_data = {
                'profile': cobbler_profile,
                'power_type': 'ssh',
                'power_user': 'root',
                'power_address': node.ip,
                'name': TaskHelper.make_slave_name(node.id, node.role),
                'hostname': node.fqdn,
                'name_servers': '\"%s\"' % settings.DNS_SERVERS,
                'name_servers_search': '\"%s\"' % settings.DNS_SEARCH,
                'netboot_enabled': '1',
                'ks_meta': {
                    'puppet_auto_setup': 1,
                    'puppet_master': settings.PUPPET_MASTER_HOST,
                    'puppet_version': settings.PUPPET_VERSION,
                    'puppet_enable': 0,
                    'mco_auto_setup': 1,
                    'install_log_2_syslog': 1,
                    'mco_pskey': settings.MCO_PSKEY,
                    'mco_vhost': settings.MCO_VHOST,
                    'mco_host': settings.MCO_HOST,
                    'mco_user': settings.MCO_USER,
                    'mco_password': settings.MCO_PASSWORD,
                    'mco_connector': settings.MCO_CONNECTOR,
                    'mco_enable': 1,
                    'auth_key': "\"%s\"" % cluster_attrs.get('auth_key', ''),
                    'ks_spaces': "\"%s\"" % json.dumps(
                        node.attributes.volumes).replace("\"", "\\\"")
                }
            }

            if node.status == "discover":
                logger.info(
                    "Node %s seems booted with bootstrap image",
                    node.id
                )
                node_data['power_pass'] = settings.PATH_TO_BOOTSTRAP_SSH_KEY
            else:
                # If it's not in discover, we expect it to be booted
                #   in target system.
                # TODO: Get rid of expectations!
                logger.info(
                    "Node %s seems booted with real system",
                    node.id
                )
                node_data['power_pass'] = settings.PATH_TO_SSH_KEY

            # FIXME: move this code (updating) into receiver.provision_resp
            if not USE_FAKE:
                node.status = "provisioning"
                db().add(node)
                db().commit()

            # here we assign admin network IPs for node
            # one IP for every node interface
            netmanager.assign_admin_ips(
                node.id,
                len(node.meta.get('interfaces', []))
            )
            admin_net_id = netmanager.get_admin_network_id()
            admin_ips = set([i.ip_addr for i in db().query(IPAddr).
                            filter_by(node=node.id).
                            filter_by(network=admin_net_id)])
            for i in node.meta.get('interfaces', []):
                if 'interfaces' not in node_data:
                    node_data['interfaces'] = {}
                node_data['interfaces'][i['name']] = {
                    'mac_address': i['mac'],
                    'static': '0',
                    'netmask': settings.ADMIN_NETWORK['netmask'],
                    'ip_address': admin_ips.pop(),
                }
                # interfaces_extra field in cobbler ks_meta
                # means some extra data for network interfaces
                # configuration. It is used by cobbler snippet.
                # For example, cobbler interface model does not
                # have 'peerdns' field, but we need this field
                # to be configured. So we use interfaces_extra
                # branch in order to set this unsupported field.
                if 'interfaces_extra' not in node_data:
                    node_data['interfaces_extra'] = {}
                node_data['interfaces_extra'][i['name']] = {
                    'peerdns': 'no',
                    'onboot': 'no'
                }

                # We want node to be able to PXE boot via any of its
                # interfaces. That is why we add all discovered
                # interfaces into cobbler system. But we want
                # assignted fqdn to be resolved into one IP address
                # because we don't completely support multiinterface
                # configuration yet.
                if i['mac'] == node.mac:
                    node_data['interfaces'][i['name']]['dns_name'] = node.fqdn
                    node_data['interfaces_extra'][i['name']]['onboot'] = 'yes'

            nodes_data.append(node_data)
            if not USE_FAKE:
                TaskHelper.prepare_syslog_dir(node)

        message = {
            'method': 'provision',
            'respond_to': 'provision_resp',
            'args': {
                'task_uuid': task.uuid,
                'engine': {
                    'url': settings.COBBLER_URL,
                    'username': settings.COBBLER_USER,
                    'password': settings.COBBLER_PASSWORD,
                },
                'nodes': nodes_data
            }
        }
        return message

    @classmethod
    def execute(cls, task):
        logger.debug("ProvisionTask.execute(task=%s)" % task.uuid)
        message = cls.message(task)
        task.cache = message
        db().add(task)
        db().commit()
        rpc.cast('naily', message)


class DeletionTask(object):

    @classmethod
    def execute(self, task, respond_to='remove_nodes_resp'):
        logger.debug("DeletionTask.execute(task=%s)" % task.uuid)
        task_uuid = task.uuid
        logger.debug("Nodes deletion task is running")
        nodes_to_delete = []
        nodes_to_delete_constant = []
        nodes_to_restore = []

        USE_FAKE = settings.FAKE_TASKS or settings.FAKE_TASKS_AMQP

        # no need to call naily if there are no nodes in cluster
        if respond_to == 'remove_cluster_resp' and \
                not list(task.cluster.nodes):
            rcvr = rpc.receiver.NailgunReceiver()
            rcvr.remove_cluster_resp(
                task_uuid=task_uuid,
                status='ready',
                progress=100
            )
            return

        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id,
                    'role': node.role
                })

                if USE_FAKE:
                    # only fake tasks
                    new_node = {}
                    keep_attrs = (
                        'id',
                        'cluster_id',
                        'role',
                        'pending_deletion',
                        'pending_addition'
                    )
                    for prop in object_mapper(node).iterate_properties:
                        if isinstance(
                            prop, ColumnProperty
                        ) and prop.key not in keep_attrs:
                            new_node[prop.key] = getattr(node, prop.key)
                    nodes_to_restore.append(new_node)
                    # /only fake tasks

        # this variable is used to iterate over it
        # and be able to delete node from nodes_to_delete safely
        nodes_to_delete_constant = list(nodes_to_delete)

        for node in nodes_to_delete_constant:
            node_db = db().query(Node).get(node['id'])

            slave_name = TaskHelper.make_slave_name(
                node['id'], node['role']
            )
            logger.debug("Removing node from database and pending it "
                         "to clean its MBR: %s", slave_name)
            if not node_db.online:
                logger.info(
                    "Node is offline, can't MBR clean: %s", slave_name)
                db().delete(node_db)
                db().commit()

                nodes_to_delete.remove(node)

        # only real tasks
        engine_nodes = []
        if not USE_FAKE:
            for node in nodes_to_delete_constant:
                slave_name = TaskHelper.make_slave_name(
                    node['id'], node['role']
                )
                logger.debug("Pending node to be removed from cobbler %s",
                             slave_name)
                engine_nodes.append(slave_name)
                try:
                    node_db = db().query(Node).get(node['id'])
                    if node_db and node_db.fqdn:
                        node_hostname = node_db.fqdn
                    else:
                        node_hostname = TaskHelper.make_slave_fqdn(
                            node['id'], node['role'])
                    logger.info("Removing node cert from puppet: %s",
                                node_hostname)
                    cmd = "puppet cert clean {0}".format(node_hostname)
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    p_stdout, p_stderr = proc.communicate()
                    logger.info(
                        "'{0}' executed, STDOUT: '{1}',"
                        " STDERR: '{2}'".format(
                            cmd,
                            p_stdout,
                            p_stderr
                        )
                    )
                except OSError:
                    logger.warning(
                        "'{0}' returned non-zero exit code".format(
                            cmd
                        )
                    )
                except Exception as e:
                    logger.warning("Exception occurred while trying to \
                            remove the system from Cobbler: '{0}'".format(
                        e.message))

        msg_delete = {
            'method': 'remove_nodes',
            'respond_to': respond_to,
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes_to_delete,
                'engine': {
                    'url': settings.COBBLER_URL,
                    'username': settings.COBBLER_USER,
                    'password': settings.COBBLER_PASSWORD,
                },
                'engine_nodes': engine_nodes
            }
        }
        # only fake tasks
        if USE_FAKE and nodes_to_restore:
            msg_delete['args']['nodes_to_restore'] = nodes_to_restore
        # /only fake tasks
        logger.debug("Calling rpc remove_nodes method")
        rpc.cast('naily', msg_delete)


class ClusterDeletionTask(object):

    @classmethod
    def execute(cls, task):
        logger.debug("Cluster deletion task is running")
        DeletionTask.execute(task, 'remove_cluster_resp')


class VerifyNetworksTask(object):

    @classmethod
    def execute(self, task, data):
        task_uuid = task.uuid
        nodes = []
        for n in task.cluster.nodes:
            node_json = {'uid': n.id, 'networks': []}
            for nic in n.interfaces:
                vlans = []
                for ng in nic.assigned_networks:
                    # Handle FuelWeb admin network first.
                    if not ng.cluster_id:
                        vlans.append(0)
                        continue
                    data_ng = filter(
                        lambda i: i['name'] == ng.name,
                        data
                    )[0]
                    vlans.extend(data_ng['vlans'])
                if not vlans:
                    continue
                node_json['networks'].append(
                    {'iface': nic.name, 'vlans': vlans}
                )
            nodes.append(node_json)

        message = {'method': 'verify_networks',
                   'respond_to': 'verify_networks_resp',
                   'args': {'task_uuid': task.uuid,
                            'nodes': nodes}}
        logger.debug("Network verification is called with: %s", message)

        task.cache = message
        db().add(task)
        db().commit()
        rpc.cast('naily', message)


class CheckNetworksTask(object):

    @classmethod
    def execute(self, task, data):
        # If not set in data then fetch from db
        if 'net_manager' in data:
            netmanager = data['net_manager']
        else:
            netmanager = task.cluster.net_manager

        if 'networks' in data:
            networks = data['networks']
        else:
            networks = map(lambda x: x.__dict__, task.cluster.network_groups)

        result = []
        err_msgs = []
        for ng in networks:
            net_errors = []
            sub_ranges = []
            ng_db = db().query(NetworkGroup).get(ng['id'])
            if not ng_db:
                net_errors.append("id")
                err_msgs.append("Invalid network ID: {0}".format(ng['id']))
            else:
                if 'cidr' in ng:
                    fnet = netaddr.IPSet([ng['cidr']])

                    if fnet & netaddr.IPSet(settings.NET_EXCLUDE):
                        net_errors.append("cidr")
                        err_msgs.append(
                            "Intersection with admin "
                            "network(s) '{0}' found".format(
                                settings.NET_EXCLUDE
                            )
                        )
                    if fnet.size < ng['network_size'] * ng['amount']:
                        net_errors.append("cidr")
                        err_msgs.append(
                            "CIDR size for network '{0}' "
                            "is less than required".format(
                                ng.get('name') or ng_db.name or ng_db.id
                            )
                        )
                # Check for intersection with Admin network
                if 'ip_ranges' in ng:
                    for k, v in enumerate(ng['ip_ranges']):
                        ip_range = netaddr.IPSet(netaddr.IPRange(v[0], v[1]))
                        admin = netaddr.IPSet(settings.NET_EXCLUDE)
                        if ip_range & admin:
                            net_errors.append("cidr")
                            err_msgs.append(
                                "IP range {0} - {1} in {2} intersects with "
                                "admin range of {3}".format(
                                    v[0], v[1],
                                    ng.get('name') or ng_db.name or ng_db.id,
                                    settings.NET_EXCLUDE
                                )
                            )
                            sub_ranges.append(k)

                if ng.get('amount') > 1 and netmanager == 'FlatDHCPManager':
                    net_errors.append("amount")
                    err_msgs.append(
                        "Network amount for '{0}' is more than 1 "
                        "while using FlatDHCP manager.".format(
                            ng.get('name') or ng_db.name or ng_db.id
                        )
                    )
            if net_errors:
                result.append({
                    "id": int(ng["id"]),
                    "ranges": sub_ranges,
                    "errors": net_errors
                })
        if err_msgs:
            task.result = result
            db().add(task)
            db().commit()
            full_err_msg = "\n".join(err_msgs)
            raise errors.NetworkCheckError(full_err_msg)


class CheckBeforeDeploymentTask(object):
    @classmethod
    def execute(cls, task):
        cls.__check_controllers_count(task)
        cls.__check_disks(task)
        cls.__check_network(task)

    @classmethod
    def __check_controllers_count(cls, task):
        controllers_count = len(
            filter(lambda node: node.role == 'controller', task.cluster.nodes))
        cluster_mode = task.cluster.mode

        if cluster_mode == 'multinode' and controllers_count < 1:
            raise errors.NotEnoughControllers(
                "Not enough controllers, %s mode requires at least 1 "
                "controller" % (cluster_mode))
        elif cluster_mode == 'ha' and controllers_count < 3:
            raise errors.NotEnoughControllers(
                "Not enough controllers, %s mode requires at least 3 "
                "controllers" % (cluster_mode))

    @classmethod
    def __check_disks(cls, task):
        for node in task.cluster.nodes:
            node.volume_manager.check_free_space()

    @classmethod
    def __check_network(cls, task):
        netmanager = NetworkManager()
        nodes_count = len(task.cluster.nodes)

        public_network = filter(
            lambda ng: ng.name == 'public',
            task.cluster.network_groups)[0]
        public_network_size = cls.__network_size(public_network)

        if public_network_size < nodes_count:
            error_message = cls.__format_network_error(nodes_count)
            raise errors.NetworkCheckError(error_message)

    @classmethod
    def __network_size(cls, network):
        size = 0
        for ip_range in network.ip_ranges:
            size += len(netaddr.IPRange(ip_range.first, ip_range.last))
        return size

    @classmethod
    def __format_network_error(cls, nodes_count):
        return 'Not enough IP addresses. Public network must have at least '\
            '{nodes_count} IP addresses '.format(nodes_count=nodes_count) +\
            'for the current environment.'


class DownloadReleaseTask(object):

    @classmethod
    def execute(cls, task, data):
        logger.debug("Download release task(uuid=%s) is running" % task.uuid)

        message = {
            'method': 'download_release',
            'respond_to': 'download_release_resp',
            'args': {
                'task_uuid': task.uuid,
                'release_info': data
            }
        }

        task.cache = message
        task.result = {'release_info': data}
        db().add(task)
        db().commit()
        cls.__update_release_state(data['release_id'])
        rpc.cast('naily', message)

    @classmethod
    def __update_release_state(cls, release_id):
        release = db().query(Release).get(release_id)
        release.state = 'downloading'
        db().commit()
