# -*- coding: utf-8 -*-

import uuid
import itertools
import logging
import traceback

import web
from sqlalchemy.orm import object_mapper, ColumnProperty

import nailgun.rpc as rpc
from nailgun.db import orm
from nailgun.settings import settings
from nailgun.notifier import notifier
from nailgun.task.errors import WrongNodeStatus
from nailgun.network import manager as netmanager
from nailgun.api.models import Base, Network, Node
from nailgun.api.validators import BasicValidator
from nailgun.provision.cobbler import Cobbler
from nailgun.task.fake import FAKE_THREADS
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import FailedProvisioning
from nailgun.task.errors import WrongNodeStatus

logger = logging.getLogger(__name__)


if settings.FAKE_TASKS:
    def fake_cast(queue, message):
        thread = FAKE_THREADS[message['method']](
            data=message
        )
        thread.start()
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
        nodes = web.ctx.orm.query(Node).filter_by(
            cluster_id=task.cluster.id,
            pending_deletion=False)

        if not settings.FAKE_TASKS:
            # only real tasks
            nodes_to_provision = []
            for node in nodes:
                if node.status == 'offline':
                    raise Exception("Node '%s' (id=%s) is in offline status."
                                    " Remove it from cluster and try again." %
                                    (node.name, node.id))
                if node.status in ('discover', 'provisioning') or \
                        (node.status == 'error' and
                         node.error_type == 'provision'):
                    nodes_to_provision.append(node)

            try:
                DeploymentTask._provision(nodes_to_provision)
            except Exception as err:
                error = "Failed to call cobbler: %s" % err.message
                logger.error("Provision error: %s\n%s",
                             error, traceback.format_exc())
                task.status = "error"
                task.message = error
                web.ctx.orm.add(task)
                web.ctx.orm.commit()
                raise FailedProvisioning(error)
            # /only real tasks

        nodes_ids = [n.id for n in nodes]
        netmanager.assign_ips(nodes_ids, "management")
        netmanager.assign_ips(nodes_ids, "public")

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            n.progress = None
            orm().add(n)
            orm().commit()
            nodes_with_attrs.append({
                'id': n.id, 'status': n.status, 'error_type': n.error_type,
                'uid': n.id, 'ip': n.ip, 'mac': n.mac, 'role': n.role,
                'network_data': netmanager.get_node_networks(n.id)
            })

        cluster_attrs = task.cluster.attributes.merged_attrs()
        nets_db = orm().query(Network).filter_by(
            cluster_id=task.cluster.id).all()

        for net in nets_db:
            cluster_attrs[net.name + '_network_range'] = net.cidr

        message = {
            'method': 'deploy',
            'respond_to': 'deploy_resp',
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes_with_attrs,
                'attributes': cluster_attrs
            }
        }
        rpc.cast('naily', message)

    @classmethod
    def _provision(cls, nodes):
        logger.info("Requested to provision nodes: %s",
                    ','.join([str(n.id) for n in nodes]))
        pd = Cobbler(settings.COBBLER_URL,
                     settings.COBBLER_USER, settings.COBBLER_PASSWORD)
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

            nd_name = TaskHelper.slave_name_by_id(node.id)

            nd_dict['hostname'] = ".".join([nd_name, settings.DNS_DOMAIN])
            nd_dict['name_servers'] = '\"%s\"' % settings.DNS_SERVERS
            nd_dict['name_servers_search'] = '\"%s\"' % settings.DNS_SEARCH

            nd_dict['interfaces'] = {
                'eth0': {
                    'mac_address': node.mac,
                    'static': '0',
                },
            }
            nd_dict['interfaces_extra'] = {
                'eth0': {
                    'peerdns': 'no'
                }
            }
            nd_dict['netboot_enabled'] = '1'
            nd_dict['ks_meta'] = """
puppet_auto_setup=1
puppet_master=%(puppet_master_host)s
puppet_version=%(puppet_version)s
puppet_enable=0
mco_auto_setup=1
install_log_2_syslog=1
mco_pskey=%(mco_pskey)s
mco_stomphost=%(mco_stomp_host)s
mco_stompport=%(mco_stomp_port)s
mco_stompuser=%(mco_stomp_user)s
mco_stomppassword=%(mco_stomp_password)s
mco_enable=1
            """ % {'puppet_master_host': settings.PUPPET_MASTER_HOST,
                   'puppet_version': settings.PUPPET_VERSION,
                   'mco_pskey': settings.MCO_PSKEY,
                   'mco_stomp_host': settings.MCO_STOMPHOST,
                   'mco_stomp_port': settings.MCO_STOMPPORT,
                   'mco_stomp_user': settings.MCO_STOMPUSER,
                   'mco_stomp_password': settings.MCO_STOMPPASSWORD,
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


class DeletionTask(object):

    @classmethod
    def execute(self, task, respond_to='remove_nodes_resp'):
        nodes_to_delete = []
        nodes_to_restore = []
        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id
                })

            if settings.FAKE_TASKS:
                # only fake tasks
                new_node = Node()
                for prop in object_mapper(new_node).iterate_properties:
                    if (isinstance(prop, ColumnProperty) and prop.key not in (
                            'id', 'cluster_id', 'role', 'pending_deletion')):
                        setattr(new_node, prop.key, getattr(node, prop.key))
                nodes_to_restore.append(new_node)

                # FIXME: it should be called in FakeDeletionThread, but
                # notifier uses web.ctx.orm, which is unavailable there.
                # Should be moved to the thread code after ORM session
                # issue is adressed
                ram = round(new_node.info.get('ram') or 0, 1)
                cores = new_node.info.get('cores') or 'unknown'
                notifier.notify("discover",
                                "New node with %s CPU core(s) "
                                "and %s GB memory is discovered" %
                                (cores, ram))
                # /only fake tasks

        # only real tasks
        if not settings.FAKE_TASKS:
            if nodes_to_delete:
                logger.debug("There are nodes to delete")
                pd = Cobbler(settings.COBBLER_URL,
                             settings.COBBLER_USER,
                             settings.COBBLER_PASSWORD
                             )
                for node in nodes_to_delete:
                    slave_name = TaskHelper.slave_name_by_id(node['id'])
                    if pd.system_exists(slave_name):
                        logger.debug("Removing system "
                                     "from cobbler: %s" % slave_name)
                        pd.remove_system(slave_name)
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
        if settings.FAKE_TASKS and nodes_to_restore:
            msg_delete['args']['nodes_to_restore'] = nodes_to_restore
        # /only fake tasks
        logger.debug("Calling rpc remove_nodes method")
        rpc.cast('naily', msg_delete)


class ClusterDeletionTask(object):

    @classmethod
    def execute(cls, task):
        DeletionTask.execute(task, 'remove_cluster_resp')


class VerifyNetworksTask(object):

    @classmethod
    def execute(self, task):
        task_uuid = task.uuid
        nets_db = orm().query(Network).filter_by(
            cluster_id=task.cluster.id).all()
        vlans_db = [net.vlan_id for net in nets_db]
        iface_db = [{'iface': 'eth0', 'vlans': vlans_db}]
        nodes = [{'networks': iface_db, 'uid': n.id}
                 for n in task.cluster.nodes]

        message = {'method': 'verify_networks',
                   'respond_to': 'verify_networks_resp',
                   'args': {'task_uuid': task.uuid,
                            'nodes': nodes}}
        rpc.cast('naily', message)
