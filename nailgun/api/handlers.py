# -*- coding: utf-8 -*-

import json
import logging

import web
import ipaddr

import settings
from helpers.vlan import VlanManager
from api.models import Release, Cluster, Node, Role, Network


def check_client_content_type(handler):
    content_type = web.ctx.env.get("CONTENT_TYPE", "application/json")
    if content_type != "application/json" \
        and web.ctx.path.startswith("/api"):
        raise web.unsupportedmediatype
    return handler()


class JSONHandler(object):
    fields = []

    @classmethod
    def render(cls, instance, fields=None):
        json_data = {}
        use_fields = fields if fields else cls.fields
        for field in use_fields:
            json_data[field] = getattr(instance, field)
        return json_data


class ClusterHandler(JSONHandler):
    fields = (
        "id",
        "name",
        "release_id"
    )

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        json_data["nodes"] = map(
            NodeHandler.render,
            instance.nodes
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
        release = web.ctx.orm.query(Release).get(data["release"])

        cluster = Cluster(
            name=data["name"],
            release=release
        )
        # TODO: discover how to add multiple objects
        if 'nodes' in data and data['nodes']:
            nodes = web.ctx.orm.query(Node).filter(
                 Node.id.in_(data['nodes'])
            )
            map(cluster.nodes.append, nodes)

        web.ctx.orm.add(cluster)
        web.ctx.orm.commit()

        network_objects = web.ctx.orm.query(Network)
        for network in release.networks_metadata:
            for nw_pool in settings.NETWORK_POOLS[network['access']]:
                nw_ip = ipaddr.IPv4Network(nw_pool)
                new_network = None
                for net in nw_ip.iter_subnets(new_prefix=24):
                    nw_exist = network_objects.filter(
                        Network.network == str(net)
                    ).first()
                    if not nw_exist:
                        new_network = net
                        break
                if new_network:
                    break

            nw = Network(
                release=release.id,
                name=network['name'],
                access=network['access'],
                network=str(new_network),
                gateway=str(new_network[1]),
                range_l=str(new_network[3]),
                range_h=str(new_network[-1]),
                vlan_id=VlanManager.generate_id(network['name'])
            )
            web.ctx.orm.add(nw)
            web.ctx.orm.commit()

        raise web.webapi.created(json.dumps(
            ClusterHandler.render(cluster),
            indent=4
        ))


class ReleaseHandler(JSONHandler):
    fields = (
        "name",
        "version",
        "description",
        "networks_metadata"
    )

    def GET(self, release_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Release)
        release = q.filter(Release.id == release_id).first()
        if not release:
            return web.notfound()
        return json.dumps(
            self.render(release),
            indent=4
        )

    def PUT(self, release_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Release)
        release = q.filter(Release.id == release_id).first()
        if not release:
            return web.notfound()
        # additional validation needed?
        data = Release.validate_json(web.data())
        # /additional validation needed?
        for key, value in data.iteritems():
            setattr(release, key, value)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(release),
            indent=4
        )

    def DELETE(self, release_id):
        release = web.ctx.orm.query(Release).filter(
            Release.id == release_id
        ).first()
        if not release:
            return web.notfound()
        web.ctx.orm.delete(release)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )



class ReleaseCollectionHandler(JSONHandler):
    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(map(
            ReleaseHandler.render,
            web.ctx.orm.query(Release).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Release.validate(web.data())
        release = Release()
        for key, value in data.iteritems():
            setattr(release, key, value)
        web.ctx.orm.add(release)
        web.ctx.orm.commit()
        raise web.webapi.created(json.dumps(
            ReleaseHandler.render(release),
            indent=4
        ))


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'roles', 'status', 'mac', 'fqdn', 'ip',
              'manufacturer', 'platform_name', 'redeployment_needed',
              'os_platform')

    def GET(self, node_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Node)
        node = q.filter(Node.id == node_id).first()
        if not node:
            return web.notfound()

        return json.dumps(
            self.render(node),
            indent=4
        )

    def PUT(self, node_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Node)
        node = q.filter(Node.id == node_id).first()
        if not node:
            return web.notfound()
        # additional validation needed?
        data = Node.validate_update(web.data())
        if not data:
            raise web.badrequest()
        # /additional validation needed?
        for key, value in data.iteritems():
            setattr(node, key, value)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(node),
            indent=4
        )

    def DELETE(self, node_id):
        node = web.ctx.orm.query(Node).filter(
            Node.id == node_id
        ).first()
        if not node:
            return web.notfound()
        web.ctx.orm.delete(node)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class NodeCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(map(
            NodeHandler.render,
            web.ctx.orm.query(Node).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Node.validate(web.data())
        node = Node()
        for key, value in data.iteritems():
            setattr(node, key, value)
        web.ctx.orm.add(node)
        web.ctx.orm.commit()
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))


class RoleCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        data = Role.validate_json(web.data())
        if 'release_id' in data:
            return json.dumps(map(
                    RoleHandler.render,
                    web.ctx.orm.query(Role).filter(
                        Role.id == data["release_id"]
                    )
                ), indent=4)

        roles = web.ctx.orm.query(Role).all()
        if 'node_id' in data:
            result = []
            for role in roles:
                # TODO role filtering
                # use request.form.cleaned_data['node_id'] to filter roles
                if False:
                    continue
                # if the role is suitable for the node, set 'available' field
                # to True. If it is not, set it to False and also describe the
                # reason in 'reason' field of rendered_role
                rendered_role = RoleHandler.render(role)
                rendered_role['available'] = True
                result.append(rendered_role)
            return json.dumps(result)
        else:
            return json.dumps(map(RoleHandler.render, roles))


class RoleHandler(JSONHandler):
    fields = ('id', 'name')

    def GET(self, role_id):
        q = web.ctx.orm.query(Role)
        role = q.filter(Role.id == role_id).first()
        if not role:
            return web.notfound()
        return json.dumps(
            self.render(role),
            indent=4
        )
