# -*- coding: utf-8 -*-

import uuid
import itertools
import logging

import web

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.network import manager as netmanager
from nailgun.api.models import Base, Network, Node
from nailgun.api.validators import BasicValidator
from nailgun.provision.cobbler import Cobbler
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import FailedProvisioning
from nailgun.task.errors import WrongNodeStatus

logger = logging.getLogger(__name__)


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
        nodes = web.ctx.orm.query(Node).filter_by(
            cluster_id=task.cluster.id,
            pending_deletion=False)

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
            task.status = "error"
            task.error = error
            web.ctx.orm.add(task)
            web.ctx.orm.commit()
            raise FailedProvisioning(error)

        netmanager.assign_ips(task.cluster.id, "management")

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            web.ctx.orm.add(n)
            web.ctx.orm.commit()
            nodes_with_attrs.append({
                'id': n.id, 'status': n.status, 'uid': n.id,
                'ip': n.ip, 'mac': n.mac, 'role': n.role,
                'network_data': netmanager.get_node_networks(n.id)
            })

        message = {
            'method': 'deploy',
            'respond_to': 'deploy_resp',
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes_with_attrs,
                'attributes': task.cluster.attributes.merged_attrs()
            }
        }
        rpc.cast('naily', message)

    @classmethod
    def _provision(cls, nodes):
        # how to do reduce in fucking python??!
        #logger.info("Requested to provision nodes:
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
                # Or, suka, s xren znaet 4em if error
                logger.info(
                    "Node %s seems booted with real system",
                    node.id
                )
                nd_dict['power_pass'] = settings.PATH_TO_SSH_KEY

            nd_dict['power_address'] = node.ip

            node.status = "provisioning"
            web.ctx.orm.add(node)
            web.ctx.orm.commit()

            nd_name = TaskHelper.slave_name_by_id(node.id)

            nd_dict['hostname'] = nd_name + settings.DNS_DOMAIN
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
    def execute(self, task):
        nodes_to_delete = []
        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id
                })

        if nodes_to_delete:
            pd = Cobbler(settings.COBBLER_URL,
                         settings.COBBLER_USER, settings.COBBLER_PASSWORD)
            for node in nodes_to_delete:
                pd.remove_system(TaskHelper.slave_name_by_id(node['id']))

            msg_delete = {
                'method': 'remove_nodes',
                'respond_to': 'remove_nodes_resp',
                'args': {
                    'task_uuid': task.uuid,
                    'nodes': nodes_to_delete
                }
            }
            rpc.cast('naily', msg_delete)


class VerifyNetworksTask(object):

    @classmethod
    def execute(self, task):
        nets_db = web.ctx.orm.query(Network).filter_by(
            cluster_id=task.cluster.id).all()
        networks = [{
            'id': n.id, 'vlan_id': n.vlan_id, 'cidr': n.cidr}
            for n in nets_db]

        nodes = [{'id': n.id, 'ip': n.ip, 'mac': n.mac, 'uid': n.id}
                 for n in task.cluster.nodes]

        message = {'method': 'verify_networks',
                   'respond_to': 'verify_networks_resp',
                   'args': {'task_uuid': task.uuid,
                            'networks': networks,
                            'nodes': nodes}}
        rpc.cast('naily', message)
