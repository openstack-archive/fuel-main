import ipaddr

from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from api.fields import RecipeField


class Recipe(models.Model):
    recipe = RecipeField(max_length=100)
    # FIXME(mihgen): depends should be recipe objects
    depends = models.CharField(max_length=100, blank=True)


class Role(models.Model):
    name = models.CharField(max_length=50)
    recipes = models.ManyToManyField(Recipe, related_name="roles")


class Release(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=30)
    description = models.TextField(null=True, blank=True)
    networks_metadata = JSONField()
    roles = models.ManyToManyField(Role, related_name='releases')

    class Meta:
        unique_together = ("name", "version")


class Cluster(models.Model):
    name = models.CharField(max_length=100)
    release = models.ForeignKey(Release, related_name='clusters')


class Node(models.Model):
    NODE_STATUSES = (
        ('offline', 'offline'),
        ('ready', 'ready'),
        ('deploying', 'deploying'),
        ('error', 'error'),
    )
    id = models.CharField(max_length=12, primary_key=True)
    cluster = models.ForeignKey(Cluster, related_name='nodes',
        null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=30, choices=NODE_STATUSES,
            default='online')
    metadata = JSONField()
    mac = models.CharField(max_length=17)
    ip = models.CharField(max_length=15)
    fqdn = models.CharField(max_length=255)

    roles = models.ManyToManyField(Role, related_name='nodes')
    new_roles = models.ManyToManyField(Role, related_name='+')
    redeployment_needed = models.BooleanField(default=False)


class IPAddr(models.Model):
    network = models.ForeignKey('Network')
    node = models.ForeignKey(Node)
    ip_addr = models.CharField(max_length=25)


class Network(models.Model):
    release = models.ForeignKey(Release, related_name="networks")
    name = models.CharField(max_length=20)
    access = models.CharField(max_length=20)
    vlan_id = models.PositiveIntegerField()
    network = models.CharField(max_length=25)
    range_l = models.CharField(max_length=25)
    range_h = models.CharField(max_length=25)
    gateway = models.CharField(max_length=25)
    nodes = models.ManyToManyField(Node, through=IPAddr)

    @property
    def netmask(self):
        return str(ipaddr.IPv4Network(self.network).netmask)

    @property
    def broadcast(self):
        return str(ipaddr.IPv4Network(self.network).broadcast)

    def update_node_network_info(self, node):
        nw = ipaddr.IPv4Network(self.network)
        range_l = ipaddr.IPv4Address(self.range_l)
        range_h = ipaddr.IPv4Address(self.range_h)
        new_ip = None
        for host in nw.iterhosts():
            if range_l <= ipaddr.IPv4Address(host) <= range_h:
                try:
                    IPAddr.objects.get(network=self, ip_addr=host)
                except IPAddr.DoesNotExist:
                    new_ip = host
                    break

        if not new_ip:
            raise Exception("There is no free IP for node %s" % node.id)

        new_ip_obj = IPAddr(network=self, ip_addr=new_ip, node=node)
        new_ip_obj.save()

        network_metadata = {
            "access": self.access,
            "vlan_id": self.vlan_id,
            "netmask": self.netmask,
            "broascast": self.broadcast,
            "gateway": self.gateway,
            "ip_addr": str(new_ip)
        }
        if "network" in node.metadata:
            node.metadata["network"][self.name] = (network_metadata)
        else:
            node.metadata["network"] = {self.name: network_metadata}
        node.save()
