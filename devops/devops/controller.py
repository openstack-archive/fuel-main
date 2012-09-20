import os
import sys
import stat
import tempfile
import shutil
import urllib
import ipaddr
import glob
import random
import string
import re
import time

from model import Node, Network
from network import IpNetworksPool
from error import DevopsError
import my_yaml

import logging

logger = logging.getLogger('devops.controller')

def randstr(length=8):
    return ''.join(random.choice(string.ascii_letters) for i in xrange(length))


class Controller:
    def __init__(self, driver):
        self.driver = driver

        self.networks_pool = IpNetworksPool()
        self._reserve_networks()

        self.home_dir = os.environ.get('DEVOPS_HOME') or\
            os.path.join(os.environ.get('APPDATA'), '.devops') or\
            os.path.join(os.environ['HOME'], ".devops")
        try:
            os.makedirs(os.path.join(self.home_dir, 'environments'), 0755)
        except OSError:
            sys.exc_clear()

    def build_environment(self, environment):
        logger.info("Building environment %s" % environment.name)
        environment.id = environment.name
        logger.debug(
            "Creating environment working directory for %s environment" % environment.name)
        environment.work_dir = os.path.join(self.home_dir, 'environments',
            environment.id)
        if os.path.isdir(environment.work_dir):
            if os.listdir(environment.work_dir):
                raise DevopsError(
                    "Working directory already exists and not emtpy: %s" % environment.work_dir)
        if not os.path.isdir(environment.work_dir):
            os.makedirs(environment.work_dir)
        logger.debug(
            "Environment working directory has been created: %s" % environment.work_dir)

        environment.driver = self.driver

        for node in environment.nodes:
            for interface in node.interfaces:
                interface.node = node
                interface.network.interfaces.append(interface)
                logger.info("Calculated interfaces '%s' '%s'" % (interface.node, interface.network.name))

            for disk in node.disks:
                if disk.base_image and disk.base_image.find('://') != -1:
                    disk.base_image = self._cache_file(disk.base_image)

            if node.cdrom:
                if node.cdrom.isopath.find('://') != -1:
                    node.cdrom.isopath = self._cache_file(node.cdrom.isopath)

        for network in environment.networks:
            logger.info("Building network %s" % network.name)

            network.ip_addresses = self.networks_pool.get()

            if network.pxe:
                network.dhcp_server = True
                tftp_path = os.path.join(environment.work_dir, "tftp")
                if not os.path.exists(tftp_path):
                    os.mkdir(tftp_path,
                        stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                network.tftp_root_dir = tftp_path

            if network.dhcp_server:
                allocated_addresses = []
                for interface in network.interfaces:
                    for address in interface.ip_addresses:
                        if address in network.ip_addresses:
                            allocated_addresses.append(address)
                logger.info("Allocate addresses are calculated for '%s'" % network.name)
                dhcp_allowed_addresses = list(network.ip_addresses)[2:-2]
                for interface in network.interfaces:
                    logger.info("Enumerated interfaces '%s' '%s'" % (interface.node, interface.network.name))
                    logger.info(list(interface.ip_addresses))
                    if not len(list(interface.ip_addresses)):
                        address = self.get_first_free_address(
                            dhcp_allowed_addresses,
                            allocated_addresses)
                        if address is None:
                            raise DevopsError, "Failed to allocate IP address for node '%s' in network '%s': no more addresses left" % (interface.node.name, network.name)
                        interface.ip_addresses.append(address)
                        logger.info("Allocate IP address '%s' for node '%s' in network '%s'" % (address, interface.node.name, network.name))
                        allocated_addresses.append(address)

                network.dhcp_dynamic_address_start = dhcp_allowed_addresses[0]
                network.dhcp_dynamic_address_end = dhcp_allowed_addresses[-1]

        for network in environment.networks:
            logger.info("Building network %s" % network.name)

            self.driver.create_network(network)
            network.driver = self.driver

        for node in environment.nodes:
            logger.info("Building node %s" % node.name)

            self._build_node(environment, node)
            node.driver = self.driver

        for network in environment.networks:
            self.driver.create_network(network)
            network.start()

        environment.built = True
        logger.info("Finished building environment %s" % environment.name)

    def destroy_environment(self, environment):
        logger.info("Destroying environment %s" % environment.name)

        for node in environment.nodes:
            logger.info("Destroying node %s" % node.name)

            node.stop()

            for snapshot in node.snapshots:
                self.driver.delete_snapshot(node, snapshot)

            for disk in node.disks:
                self.driver.delete_disk(disk)

            self.driver.delete_node(node)
            del node.driver

        for network in environment.networks:
            logger.info("Destroying network %s" % network.name)

            network.stop()
            self.driver.delete_network(network)
            del network.driver

            # FIXME
            try:
                self.networks_pool.put(network.ip_addresses)
            except:
                pass

        del environment.driver

        logger.info("Removing environment %s files" % environment.name)

        shutil.rmtree(environment.work_dir)

        logger.info("Finished destroying environment %s" % environment.name)

    def load_environment(self, environment_id):
        env_work_dir = os.path.join(
            self.home_dir, 'environments',
            environment_id)
        env_config_file = os.path.join(env_work_dir, 'config')
        if not os.path.exists(env_config_file):
            raise DevopsError, "Environment '%s' couldn't be found" % environment_id

        with file(env_config_file) as f:
            data = f.read()

        environment = my_yaml.load(data)

        return environment

    def save_environment(self, environment):
        data = my_yaml.dump(environment)
        if not environment.built:
            raise DevopsError, "Environment has not been built yet."
        with file(os.path.join(environment.work_dir, 'config'), 'w') as f:
            f.write(data)

    @property
    def saved_environments(self):
        saved_environments = []
        for path in glob.glob(os.path.join(self.home_dir, 'environments', '*')):
            if os.path.exists(os.path.join(path, 'config')):
                saved_environments.append(os.path.basename(path))
        return saved_environments

    def _reserve_networks(self):
        logger.debug("Scanning for ip networks that are already taken")
        allocated_networks = self.driver.get_allocated_networks()
        if allocated_networks:
            for network in allocated_networks:
                logger.debug("Reserving ip network %s" % network)
                self.networks_pool.reserve(ipaddr.IPNetwork(network))
#       todo use settings
        with os.popen("ip route") as f:
            for line in f:
                words = line.split()
                if len(words) == 0:
                    continue
                if words[0] == 'default':
                    continue
                address = ipaddr.IPv4Network(words[0])
                logger.debug("Reserving ip network %s" % address)
                self.networks_pool.reserve(address)

        logger.debug("Finished scanning for taken ip networks")

    def _build_node(self, environment, node):
        for disk in filter(lambda d: d.path is None, node.disks):
            logger.debug("Creating disk file for node '%s'" % node.name)
            disk.path = self.driver.create_disk(disk)

        logger.debug("Creating node '%s'" % node.name)
        self.driver.create_node(node)

    def _cache_file(self, url):
        cache_dir = os.path.join(self.home_dir, 'cache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, 0755)

        cache_log_path = os.path.join(cache_dir, 'entries')
        if os.path.exists(cache_log_path):
            with file(cache_log_path) as f:
                cache_entries = my_yaml.load(f.read())
        else:
            cache_entries = dict()

        ext_cache_log_path = os.path.join(cache_dir, 'extended_entries')
        if os.path.exists(ext_cache_log_path):
            with file(ext_cache_log_path) as f:
                extended_cache_entries = my_yaml.load(f.read())
        else:
            extended_cache_entries = dict()
        for key, value in cache_entries.items():
            if not extended_cache_entries.has_key(key):
                extended_cache_entries[key] = {'cached-path': value}

        RFC1123_DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'
        url_attrs = {}
        cached_path = ''
        local_mtime = 0

        if extended_cache_entries.has_key(url):
            url_attrs = extended_cache_entries[url]
            cached_path = url_attrs['cached-path']

            if url_attrs.has_key('last-modified'):
                local_mtime = time.mktime(
                    time.strptime(url_attrs['last-modified'],
                        RFC1123_DATETIME_FORMAT))

        else:
            logger.debug("Cache miss for '%s', downloading" % url)

        remote = urllib.urlopen(url)
        msg = remote.info()
        if msg.has_key('last-modified'):
            url_mtime = time.mktime(
                time.strptime(msg['last-modified'], RFC1123_DATETIME_FORMAT))
        else:
            url_mtime = 0

        if local_mtime >= url_mtime:
            logger.debug("Cache is up to date for '%s': '%s'" % (
                url, cached_path))
            return cached_path

        elif cached_path != '':
            logger.debug("Cache is old for '%s', downloading" % url)

        if not os.access(cached_path, os.W_OK):
            try:
                os.unlink(cached_path)
            except Exception:
                pass
            fd, cached_path = tempfile.mkstemp(prefix=cache_dir + '/')
            os.close(fd)

            with file(cached_path, 'w') as f:
                shutil.copyfileobj(remote, f)

            os.chmod(
                cached_path,
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

        if msg.has_key('last-modified'):
            url_attrs['last-modified'] = msg['last-modified']
        url_attrs['cached-path'] = cached_path
        extended_cache_entries[url] = url_attrs

        with file(ext_cache_log_path, 'w') as f:
            f.write(my_yaml.dump(extended_cache_entries))

        cache_entries[url] = cached_path

        with file(cache_log_path, 'w') as f:
            f.write(my_yaml.dump(cache_entries))

        logger.debug("Cached '%s' to '%s'" % (url, cached_path))

        return cached_path

    def get_first_free_address(self, allowed_addresses, allocated_addresses):
        s = set(allocated_addresses)
        for x in allowed_addresses:
            if x not in s:
                return x
        return None
