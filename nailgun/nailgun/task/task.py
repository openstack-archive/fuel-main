# -*- coding: utf-8 -*-

import uuid
import itertools
import traceback
import subprocess
import shlex
import shutil
import os

import web
import netaddr
from sqlalchemy.orm import object_mapper, ColumnProperty

import nailgun.rpc as rpc
from nailgun.db import orm
from nailgun.logger import logger
from nailgun.settings import settings
from nailgun.notifier import notifier
from nailgun.task.helpers import update_task_status
from nailgun.network.manager import NetworkManager
from nailgun.api.models import Base
from nailgun.api.models import Network
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.api.models import IPAddr
from nailgun.api.validators import BasicValidator
from nailgun.provision.cobbler import Cobbler
from nailgun.task.fake import FAKE_THREADS

from nailgun.errors import errors


def fake_cast(queue, message, **kwargs):
    thread = FAKE_THREADS[message['method']](
        data=message,
        params=kwargs
    )
    thread.start()
    thread.name = message['method'].upper()


if settings.FAKE_TASKS or settings.FAKE_TASKS_AMQP:
    rpc.cast = fake_cast


class TaskHelper(object):

    @classmethod
    def slave_name_by_id(cls, id):
        return "slave-%s" % str(id)


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
#   A: offline-when node doesn't respond (agent doesn't run, not implemented);
#              let's say user should remove this node from cluster before
#              deployment.
#      ready - target OS is loaded and node is Ok, we can just redeploy
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
    def execute(cls, task):
        task_uuid = task.uuid
        cluster_id = task.cluster.id
        netmanager = NetworkManager()
        nodes = orm().query(Node).filter_by(
            cluster_id=task.cluster.id,
            pending_deletion=False).order_by(Node.id)

        for node in nodes:
            nd_name = TaskHelper.slave_name_by_id(node.id)
            node.fqdn = ".".join([nd_name, settings.DNS_DOMAIN])
            orm().add(node)
            orm().commit()
        fqdns = ','.join([n.fqdn for n in nodes])
        logger.info("Associated FQDNs to nodes: %s" % fqdns)

        if not settings.FAKE_TASKS and not settings.FAKE_TASKS_AMQP:
            logger.info("Entered to processing of 'real' tasks, not 'fake'..")
            nodes_to_provision = []
            for node in nodes:
                if not node.online:
                    raise errors.NodeOffline(
                        "Node '%s' (id=%s) is offline."
                        " Remove it from environment and try again." %
                        (node.name, node.id)
                    )
                if node.status in ('discover', 'provisioning') or \
                        (node.status == 'error' and
                         node.error_type == 'provision'):
                    nodes_to_provision.append(node)

            try:
                DeploymentTask._provision(nodes_to_provision, netmanager)
            except Exception as err:
                error = "Failed to call cobbler: {0}".format(
                    str(err) or "see logs for details"
                )
                logger.error("Provision error: %s\n%s",
                             error, traceback.format_exc())
                update_task_status(task.uuid, "error", 100, error)
                raise errors.FailedProvisioning(error)
            # /only real tasks

        nodes_ids = [n.id for n in nodes]
        logger.info("Assigning IP addresses to nodes..")
        netmanager.assign_ips(nodes_ids, "management")
        netmanager.assign_ips(nodes_ids, "public")

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            if n.status in ('ready', 'deploying'):
                n.status = 'provisioned'
            n.progress = 0
            orm().add(n)
            orm().commit()
            nodes_with_attrs.append({
                'id': n.id, 'status': n.status, 'error_type': n.error_type,
                'uid': n.id, 'ip': n.ip, 'mac': n.mac, 'role': n.role,
                'fqdn': n.fqdn, 'progress': n.progress, 'meta': n.meta,
                'network_data': netmanager.get_node_networks(n.id),
                'online': n.online
            })

        cluster_attrs = task.cluster.attributes.merged_attrs_values()

        nets_db = orm().query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).all()

        ng_db = orm().query(NetworkGroup).filter_by(
            cluster_id=cluster_id).all()
        for net in ng_db:
            cluster_attrs[net.name + '_network_range'] = net.cidr

        fixed_net = orm().query(NetworkGroup).filter_by(
            cluster_id=cluster_id).filter_by(
                name='fixed').first()

        cluster_attrs['network_manager'] = task.cluster.net_manager
        if task.cluster.net_manager == "VlanManager":
            cluster_attrs['vlan_interface'] = 'eth0'
            cluster_attrs['network_size'] = fixed_net.network_size
            cluster_attrs['num_networks'] = fixed_net.amount
            cluster_attrs['vlan_start'] = fixed_net.vlan_start

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
        task.cache = message
        orm().add(task)
        orm().commit()
        rpc.cast('naily', message)

    @classmethod
    def _prepare_syslog_dir(cls, node, prefix=None):
        if not prefix:
            prefix = settings.SYSLOG_DIR

        old = os.path.join(prefix, node.ip)
        bak = os.path.join(prefix, "%s.bak" % node.fqdn)
        new = os.path.join(prefix, node.fqdn)
        links = map(
            lambda i: os.path.join(prefix, *i),
            orm().query(IPAddr.ip_addr).
            filter_by(node=node.id).
            filter_by(admin=True)
        )
        # backup directory if it exists
        if os.path.isdir(new):
            if os.path.islink(bak):
                os.unlink(bak)
            elif os.path.isdir(bak):
                shutil.rmtree(bak)
            os.rename(new, bak)
        # rename bootstrap directory into fqdn
        if os.path.islink(old):
            os.unlink(old)
        if os.path.isdir(old):
            os.rename(old, new)
        else:
            os.makedirs(new)
        # creating symlinks
        for l in links:
            if os.path.islink(l) or os.path.isfile(l):
                os.unlink(l)
            if os.path.isdir(l):
                shutil.rmtree(l)
            os.symlink(new, l)
        os.system("/usr/bin/pkill -HUP rsyslog")

    @classmethod
    def _provision(cls, nodes, netmanager):
        logger.info("Requested to provision nodes: %s",
                    ','.join([str(n.id) for n in nodes]))
        pd = Cobbler(
            settings.COBBLER_URL,
            settings.COBBLER_USER,
            settings.COBBLER_PASSWORD,
            logger=logger
        )
        nd_dict = {
            'profile': settings.COBBLER_PROFILE,
            'power_type': 'ssh',
            'power_user': 'root',
        }

        for node in nodes:
            if node.status == "discover":
                logger.info(
                    "Node %s seems booted with bootstrap image",
                    node.id
                )
                nd_dict['power_pass'] = settings.PATH_TO_BOOTSTRAP_SSH_KEY
            else:
                # If it's not in discover, we expect it to be booted
                #   in target system.
                # TODO: Get rid of expectations!
                logger.info(
                    "Node %s seems booted with real system",
                    node.id
                )
                nd_dict['power_pass'] = settings.PATH_TO_SSH_KEY

            nd_dict['power_address'] = node.ip

            node.status = "provisioning"
            orm().add(node)
            orm().commit()

            nd_name = node.fqdn.split('.')[0]

            nd_dict['hostname'] = node.fqdn
            nd_dict['name_servers'] = '\"%s\"' % settings.DNS_SERVERS
            nd_dict['name_servers_search'] = '\"%s\"' % settings.DNS_SEARCH

            netmanager.assign_admin_ips(
                node.id,
                len(node.meta.get('interfaces', []))
            )
            admin_ips = set([i.ip_addr for i in orm().query(IPAddr).
                            filter_by(node=node.id).
                            filter_by(admin=True)])
            for i in node.meta.get('interfaces', []):
                if 'interfaces' not in nd_dict:
                    nd_dict['interfaces'] = {}
                nd_dict['interfaces'][i['name']] = {
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
                if 'interfaces_extra' not in nd_dict:
                    nd_dict['interfaces_extra'] = {}
                nd_dict['interfaces_extra'][i['name']] = {
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
                    nd_dict['interfaces'][i['name']]['dns_name'] = node.fqdn
                    nd_dict['interfaces_extra'][i['name']]['onboot'] = 'yes'

            cluster_attrs = node.cluster.attributes.merged_attrs_values()

            nd_dict['netboot_enabled'] = '1'
            nd_dict['ks_meta'] = """
puppet_auto_setup=1
puppet_master=%(puppet_master_host)s
puppet_version=%(puppet_version)s
puppet_enable=0
mco_auto_setup=1
install_log_2_syslog=1
mco_pskey=%(mco_pskey)s
mco_vhost=%(mco_vhost)s
mco_host=%(mco_host)s
mco_user=%(mco_user)s
mco_password=%(mco_password)s
mco_connector=%(mco_connector)s
mco_enable=1
auth_key="%(auth_key)s"
            """ % {'puppet_master_host': settings.PUPPET_MASTER_HOST,
                   'puppet_version': settings.PUPPET_VERSION,
                   'mco_pskey': settings.MCO_PSKEY,
                   'mco_host': settings.MCO_HOST,
                   'mco_vhost': settings.MCO_VHOST,
                   'mco_user': settings.MCO_USER,
                   'mco_connector': settings.MCO_CONNECTOR,
                   'mco_password': settings.MCO_PASSWORD,
                   'auth_key': cluster_attrs.get('auth_key', '')
                   }

            logger.debug("Node %s\nks_meta without extra params: %s" %
                         (nd_name, nd_dict['ks_meta']))
            logger.debug(
                "Trying to save node %s into provision system: profile: %s ",
                node.id,
                nd_dict.get('profile', 'unknown')
            )
            pd.item_from_dict('system', nd_name, nd_dict, False, False)
            logger.debug(
                "Trying to reboot node %s using %s "
                "in order to launch provisioning",
                node.id,
                nd_dict.get('power_type', 'unknown')
            )
            pd.power_reboot(nd_name)
            cls._prepare_syslog_dir(node)
        pd.sync()


class DeletionTask(object):

    @classmethod
    def execute(self, task, respond_to='remove_nodes_resp'):
        task_uuid = task.uuid
        logger.debug("Nodes deletion task is running")
        nodes_to_delete = []
        nodes_to_restore = []

        USE_FAKE = settings.FAKE_TASKS or settings.FAKE_TASKS_AMQP

        # no need to call naily if there are no nodes in cluster
        if respond_to == 'remove_cluster_resp' and \
                not list(task.cluster.nodes):
            rcvr = rpc.receiver.NailgunReceiver()
            rcvr.initialize()
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
                    'uid': node.id
                })

                if USE_FAKE:
                    # only fake tasks
                    new_node = Node()
                    keep_attrs = (
                        'id',
                        'cluster_id',
                        'role',
                        'pending_deletion',
                        'pending_addition'
                    )
                    for prop in object_mapper(new_node).iterate_properties:
                        if isinstance(
                            prop, ColumnProperty
                        ) and prop.key not in keep_attrs:
                            setattr(
                                new_node,
                                prop.key,
                                getattr(node, prop.key)
                            )
                    nodes_to_restore.append(new_node)
                    # /only fake tasks

        # only real tasks
        if not USE_FAKE:
            if nodes_to_delete:
                logger.debug("There are nodes to delete")
                pd = Cobbler(
                    settings.COBBLER_URL,
                    settings.COBBLER_USER,
                    settings.COBBLER_PASSWORD
                )
                for node in nodes_to_delete:
                    slave_name = TaskHelper.slave_name_by_id(node['id'])
                    if pd.system_exists(slave_name):
                        logger.debug("Removing system "
                                     "from cobbler: %s" % slave_name)
                        pd.remove_system(slave_name)
                    try:
                        logger.info("Deleting old certs from puppet..")
                        node_db = orm().query(Node).get(node['id'])
                        if node_db and node_db.fqdn:
                            node_hostname = node_db.fqdn
                        else:
                            node_hostname = '.'.join([
                                slave_name, settings.DNS_DOMAIN])
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

        # /only real tasks

        msg_delete = {
            'method': 'remove_nodes',
            'respond_to': respond_to,
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes_to_delete,
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
        vlans = [int(d['vlan_id']) for d in data]

        nodes = []
        for n in task.cluster.nodes:
            iface = 'eth0'

            for i in n.meta.get('interfaces', []):
                if i['mac'] == n.mac:
                    iface = i['name']
                    break
            nodes.append({
                'uid': n.id,
                'networks': [
                    {
                        'iface': iface,
                        'vlans': vlans
                    }
                ]
            })

        message = {'method': 'verify_networks',
                   'respond_to': 'verify_networks_resp',
                   'args': {'task_uuid': task.uuid,
                            'nodes': nodes}}
        logger.debug("Network verification is called with: %s", message)

        task.cache = message
        orm().add(task)
        orm().commit()
        rpc.cast('naily', message)


class CheckNetworksTask(object):

    @classmethod
    def execute(self, task, data):
        task_uuid = task.uuid
        netmanager = task.cluster.net_manager
        result = []
        err_msgs = []
        for ng in data:
            net_errors = []
            ng_db = orm().query(NetworkGroup).get(ng['id'])
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
                    "errors": net_errors
                })
        if err_msgs:
            task.result = result
            orm().add(task)
            orm().commit()
            full_err_msg = "\n".join(err_msgs)
            raise errors.NetworkCheckError(full_err_msg)
