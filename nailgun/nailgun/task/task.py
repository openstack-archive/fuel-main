# -*- coding: utf-8 -*-

import uuid
import itertools
import logging

import web
from sqlalchemy import Column
from sqlalchemy import Integer, String, Unicode, Text, Boolean
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import relationship, backref

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.network import manager as netmanager
from nailgun.api.models import Base, Network
from nailgun.api.validators import BasicValidator
from nailgun.provision.cobbler import Cobbler
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import FailedProvisioning
from nailgun.task.errors import WrongNodeStatus

logger = logging.getLogger(__name__)


class DeploymentTask(object):

    @classmethod
    def execute(cls, task):
        try:
            pd = Cobbler(settings.COBBLER_URL,
                         settings.COBBLER_USER, settings.COBBLER_PASSWORD)
        except Exception as err:
            error = "Failed to call cobbler: %s" % err.message
            task.status = "error"
            task.error = error
            web.ctx.orm.add(task)
            web.ctx.orm.commit()
            raise FailedProvisioning(error)

        nd_dict = {
            'profile': settings.COBBLER_PROFILE,
            'power_type': 'ssh',
            'power_user': 'root',
        }

        allowed_statuses = ("discover", "ready")
        error_nodes = []
        for node in task.cluster.nodes:
            if node.status not in allowed_statuses:
                if node.pending_deletion:
                    continue
                else:
                    error_nodes.append(node)

        if error_nodes:
            errorlist = []
            for node in error_nodes:
                errorlist.append(
                    "Node %s (%s) status:%s not in %s" % (
                        node.mac,
                        node.ip,
                        node.status,
                        str(allowed_statuses)
                    )
                )
            err = "\n".join(errorlist)
            task.status = "error"
            task.error = err
            web.ctx.orm.add(task)
            web.ctx.orm.commit()
            raise WrongNodeStatus(err)

        for node in itertools.ifilter(
            lambda n: n.status in allowed_statuses, task.cluster.nodes
        ):
            if node.status == "discover":
                logger.info(
                    "Node %s seems booted with bootstrap image",
                    node.id
                )
                nd_dict['power_pass'] = settings.PATH_TO_BOOTSTRAP_SSH_KEY
            else:
                logger.info(
                    "Node %s seems booted with real system",
                    node.id
                )
                nd_dict['power_pass'] = settings.PATH_TO_SSH_KEY

            nd_dict['power_address'] = node.ip

            node.status = "provisioning"
            node.redeployment_needed = False
            web.ctx.orm.add(node)
            web.ctx.orm.commit()

            nd_name = "slave-%d" % node.id

            nd_dict['hostname'] = 'slave-%d.%s' % \
                (node.id, settings.DNS_DOMAIN)
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

        netmanager.assign_ips(task.cluster.id, "management")

        nodes = []
        for n in task.cluster.nodes:
            if not node.pending_deletion:
                nodes.append({
                    'id': n.id, 'status': n.status, 'uid': n.id,
                    'ip': n.ip, 'mac': n.mac, 'role': n.role,
                    'network_data': netmanager.get_node_networks(n.id)
                })

        message = {
            'method': 'deploy',
            'respond_to': 'deploy_resp',
            'args': {
                'task_uuid': task.uuid,
                'nodes': nodes,
                'attributes': task.cluster.attributes.merged_attrs()
            }
        }
        rpc.cast('naily', message)


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
