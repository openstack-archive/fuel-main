# -*- coding: utf-8 -*-

import uuid
import logging
import itertools

logger = logging.getLogger(__name__)

import web
from nailgun.settings import settings
from nailgun.api.models import Task, Cluster
from nailgun.provision.cobbler import Cobbler
from nailgun.taskmanager.errors import DeploymentAlreadyStarted
from nailgun.taskmanager.errors import FailedProvisioning
from nailgun.taskmanager.errors import WrongNodeStatus


class TaskManager(object):

    def __init__(self, cluster=None, cluster_id=None):
        if not cluster and not cluster_id:
            raise ValueError("Cluster or cluster ID should be specified")
        if cluster:
            self.cluster = cluster
        else:
            self.cluster = orm.query(Cluster).get(cluster_id)


class DeploymentTaskManager(TaskManager):

    def start_deployment(self):
        q = web.ctx.orm.query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == "super"
        )
        for t in q:
            if t.status == "running":
                raise DeploymentAlreadyStarted()
            elif t.status in ("ready", "error"):
                web.ctx.orm.delete(t)
                web.ctx.orm.commit()
        self.super_task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster=self.cluster
        )
        web.ctx.orm.add(self.super_task)
        web.ctx.orm.commit()
        self.deployment_task = self.super_task.create_subtask("deployment")
        self.deletion_task = self.super_task.create_subtask("deletion")
        self.start_provisioning()
        return self.super_task

    def start_provisioning(self):
        try:
            pd = Cobbler(settings.COBBLER_URL,
                         settings.COBBLER_USER, settings.COBBLER_PASSWORD)
        except Exception as err:
            error = "Failed to call cobbler: %s" % err.message
            self.deployment_task.status = "error"
            self.deployment_task.error = error
            self.super_task.refresh()
            web.ctx.orm.add(self.deployment_task)
            web.ctx.orm.commit()
            raise FailedProvisioning(error)

        nd_dict = {
            'profile': settings.COBBLER_PROFILE,
            'power_type': 'ssh',
            'power_user': 'root',
        }

        allowed_statuses = ("discover", "ready")
        for node in self.cluster.nodes:
            if node.status not in allowed_statuses:
                if node.pending_deletion:
                    continue
                else:
                    err = "Node %s (%s) status:%s not in %s" % (
                        node.mac,
                        node.ip,
                        node.status,
                        str(allowed_statuses)
                    )
                    self.deployment_task.status = "error"
                    self.deployment_task.error = err
                    self.super_task.refresh()
                    web.ctx.orm.add(task)
                    web.ctx.orm.commit()
                    raise WrongNodeStatus(err)

        for node in itertools.ifilter(
            lambda n: n.status in allowed_statuses, self.cluster.nodes
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
