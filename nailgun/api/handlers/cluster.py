# -*- coding: utf-8 -*-

import json
import uuid
import logging
import itertools

import web
import netaddr

import rpc
from settings import settings
from api.models import Cluster, Node, Network, Release, Attributes, IPAddr
from api.models import Vlan, Task
from api.handlers.base import JSONHandler
from api.handlers.node import NodeHandler
from api.handlers.tasks import TaskHandler
from provision.cobbler import Cobbler
from network import manager as netmanager


class ClusterHandler(JSONHandler):
    fields = (
        "id",
        "name",
        "type",
        "mode",
        "redundancy",
        ("nodes", "*"),
        ("release", "*")
    )
    model = Cluster

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        json_data["tasks"] = map(
            TaskHandler.render,
            instance.tasks
        )
        return json_data

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster)
        cluster = q.filter(Cluster.id == cluster_id).first()
        if not cluster:
            return web.notfound()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster).filter(Cluster.id == cluster_id)
        cluster = q.first()
        if not cluster:
            return web.notfound()
        # additional validation needed?
        data = Cluster.validate_json(web.data())
        # /additional validation needed?
        for key, value in data.iteritems():
            if key == "nodes":
                map(cluster.nodes.remove, cluster.nodes)
                nodes = web.ctx.orm.query(Node).filter(
                    Node.id.in_(value)
                )
                map(cluster.nodes.append, nodes)
            else:
                setattr(cluster, key, value)
        web.ctx.orm.add(cluster)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def DELETE(self, cluster_id):
        cluster = web.ctx.orm.query(Cluster).filter(
            Cluster.id == cluster_id
        ).first()
        if not cluster:
            return web.notfound()
        web.ctx.orm.delete(cluster)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class ClusterCollectionHandler(JSONHandler):
    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(map(
            ClusterHandler.render,
            web.ctx.orm.query(Cluster).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Cluster.validate(web.data())

        cluster = Cluster()
        cluster.release = web.ctx.orm.query(Release).get(data["release"])

        # TODO: discover how to add multiple objects
        if 'nodes' in data and data['nodes']:
            nodes = web.ctx.orm.query(Node).filter(
                Node.id.in_(data['nodes'])
            )
            map(cluster.nodes.append, nodes)

        # TODO: use fields
        for field in ('name', 'type', 'mode', 'redundancy'):
            setattr(cluster, field, data.get(field))

        web.ctx.orm.add(cluster)
        web.ctx.orm.commit()
        attributes = Attributes(
            editable=cluster.release.attributes_metadata.get("editable"),
            generated=cluster.release.attributes_metadata.get("generated"),
            cluster=cluster
        )
        web.ctx.orm.add(attributes)
        web.ctx.orm.commit()
        attributes.generate_fields()
        web.ctx.orm.add(attributes)
        web.ctx.orm.commit()

        used_nets = [n.cidr for n in web.ctx.orm.query(Network).all()]
        used_vlans = [v.id for v in web.ctx.orm.query(Vlan).all()]

        for network in cluster.release.networks_metadata:
            new_vlan = sorted(list(set(settings.VLANS) - set(used_vlans)))[0]
            vlan_db = Vlan(id=new_vlan)
            web.ctx.orm.add(vlan_db)
            web.ctx.orm.commit()

            pool = settings.NETWORK_POOLS[network['access']]
            nets_free_set = netaddr.IPSet(pool) -\
                netaddr.IPSet(settings.NET_EXCLUDE) -\
                netaddr.IPSet(used_nets)

            free_cidrs = sorted(list(nets_free_set._cidrs))
            new_net = list(free_cidrs[0].subnet(24, count=1))[0]

            nw_db = Network(
                release=cluster.release.id,
                name=network['name'],
                access=network['access'],
                cidr=str(new_net),
                gateway=str(new_net[1]),
                cluster_id=cluster.id,
                vlan_id=vlan_db.id
            )
            web.ctx.orm.add(nw_db)
            web.ctx.orm.commit()

            used_vlans.append(new_vlan)
            used_nets.append(str(new_net))

        raise web.webapi.created(json.dumps(
            ClusterHandler.render(cluster),
            indent=4
        ))


class ClusterChangesHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster).filter(Cluster.id == cluster_id)
        cluster = q.first()
        if not cluster:
            return web.notfound()

        q = web.ctx.orm.query(Task).filter(
            Task.cluster == cluster,
            Task.name == "deploy"
        )
        for t in q:
            if t.status == "running":
                raise web.badrequest(
                    "Deploying has been already started"
                )
            elif t.status in ("ready", "error"):
                web.ctx.orm.delete(t)
                web.ctx.orm.commit()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="deploy",
            cluster=cluster
        )
        web.ctx.orm.add(task)
        web.ctx.orm.commit()

        try:
            pd = Cobbler(settings.COBBLER_URL,
                         settings.COBBLER_USER, settings.COBBLER_PASSWORD)
        except Exception as err:
            task.status = "error"
            task.error = "Failed to start provisioning"
            web.ctx.orm.add(task)
            web.ctx.orm.commit()
            raise web.badrequest(str(err))

        nd_dict = {
            'profile': settings.COBBLER_PROFILE,
            'power_type': 'ssh',
            'power_user': 'root',
        }

        allowed_statuses = ("discover", "ready")
        for node in cluster.nodes:
            if node.status not in allowed_statuses:
                err = "Node %s (%s) status:%s not in %s" % (
                    node.mac,
                    node.ip,
                    node.status,
                    str(allowed_statuses)
                )
                task.status = "error"
                task.error = err
                web.ctx.orm.add(task)
                web.ctx.orm.commit()
                raise web.badrequest()

        for node in itertools.ifilter(
            lambda n: n.status in allowed_statuses, cluster.nodes
        ):
            if node.status == "discover":
                logging.info(
                    "Node %s seems booted with bootstrap image",
                    node.id
                )
                nd_dict['power_pass'] = 'rsa:%s' % \
                    settings.PATH_TO_BOOTSTRAP_SSH_KEY
            else:
                logging.info(
                    "Node %s seems booted with real system",
                    node.id
                )
                nd_dict['power_pass'] = 'rsa:%s' % settings.PATH_TO_SSH_KEY

            nd_dict['power_address'] = node.ip

            node.status = "provisioning"
            web.ctx.orm.add(node)
            web.ctx.orm.commit()

            nd_name = "%d_%s." % (node.id, node.mac)

            nd_dict['hostname'] = 'slave-%s.%s' % \
                (node.mac.replace(':', ''), settings.DNS_DOMAIN)
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
            nd_dict['ks_meta'] = "\"puppet_auto_setup=1 \
puppet_master=%(puppet_master_host)s \
puppet_version=%(puppet_version) \
puppet_enable=0 \
mco_auto_setup=1 \
mco_pskey=%(mco_pskey)s \
mco_stomphost=%(mco_stomphost)s \
mco_stompport=%(mco_stompport)s \
mco_stompuser=%(mco_stompuser)s \
mco_stomppassword=%(mco_stompassword)s \
mco_enable=1\"" % {'puppet_master_host': settings.PUPPET_MASTER_HOST,
                   'puppet_version': settings.PUPPET_VERSION,
                   'mco_pskey': settings.MCO_PSKEY,
                   'mco_stomphost': settings.MCO_STOMPHOST,
                   'mco_stompport': settings.MCO_STOMPPORT,
                   'mco_stompuser': settings.MCO_STOMPUSER,
                   'mco_stompassword': settings.MCO_STOMPPASSWORD,
                   }

            logging.debug(
                "Trying to save node %s into provision system: profile: %s ",
                node.id,
                nd_dict.get('profile', 'unknown')
            )
            pd.item_from_dict('system', nd_name, nd_dict, False, False)
            logging.debug(
                "Trying to reboot node %s using %s "
                "in order to launch provisioning",
                node.id,
                nd_dict.get('power_type', 'unknown')
            )
            pd.power_on(nd_name)

        netmanager.assign_ips(cluster_id, "management")

        nodes = []
        for n in cluster.nodes:
            nodes.append({'id': n.id, 'status': n.status,
                          'ip': n.ip, 'mac': n.mac, 'role': n.role,
                          'network_data': netmanager.get_node_networks(n.id)})
        message = {'method': 'deploy',
                   'respond_to': 'deploy_resp',
                   'args': {'task_uuid': task.uuid, 'nodes': nodes}}
        rpc.cast('naily', message)

        return json.dumps(
            TaskHandler.render(task),
            indent=4
        )


class ClusterNetworksHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster).filter(Cluster.id == cluster_id)
        cluster = q.first()
        if not cluster:
            return web.notfound()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="verify_networks",
            cluster=cluster
        )
        web.ctx.orm.add(task)
        web.ctx.orm.commit()

        nets_db = web.ctx.orm.query(Network).filter_by(
            cluster_id=cluster_id).all()
        networks = [{
            'id': n.id, 'vlan_id': n.vlan_id, 'cidr': n.cidr}
            for n in nets_db]

        nodes = [{'id': n.id, 'ip': n.ip, 'mac': n.mac} for n in cluster.nodes]

        message = {'method': 'verify_networks',
                   'respond_to': 'verify_networks_resp',
                   'args': {'task_uuid': task.uuid,
                            'networks': networks,
                            'nodes': nodes}}
        rpc.cast('naily', message)

        return json.dumps(
            self.render(cluster),
            indent=4
        )


class ClusterAttributesHandler(JSONHandler):
    fields = (
        "editable",
    )

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster).filter(Cluster.id == cluster_id)
        cluster = q.first()
        if not cluster:
            return web.notfound()

        attrs = cluster.attributes
        if not attrs:
            return web.notfound()

        return json.dumps(
            {
                "editable": attrs.editable
            },
            indent=4
        )
