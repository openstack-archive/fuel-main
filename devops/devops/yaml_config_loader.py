
import yaml
import re
from model import Environment, Network, Node

class ConfigError(Exception): pass

def load(stream):
    data = yaml.load(stream)

    if not data.has_key('nodes'):
        raise ConfigError, "No nodes defined"

    environment = Environment()

    if data.has_key('networks'):
        for network_data in data['networks']:
            parse_network(environment, network_data)

    for node_data in data['nodes']:
        parse_node(environment, node_data)

    return environment 


def dump(stream):
    raise "Not implemented yet"

def parse_network(environment, data):
    if data.has_key('name'):
        name = data['name']
    elif data.has_key('network'):
        name = data['network']
    else:
        raise ConfigError, "Unnamed network"

    network = Network(name)
    network.kind = 'hostonly'
    if data.has_key('type'):
        kind = data['type']
        if not kind in ['hostonly', 'bridged']:
            raise ConfigError, "Unknown network type: %s" % t

        network.kind = kind

    for existing_network in environment.networks:
        if existing_network.name == network.name:
            raise ConfigError, "Network with given name already exists: %s" % network.name

    environment.networks.append(network)

    return network

def parse_node(environment, data):
    if data.has_key('name'):
        name = data['name']
    elif data.has_key('node'):
        name = data['node']
    else:
        raise ConfigError, "Unnamed node"

    node = Node(name)
    if data.has_key('cpu'):
        node.cpu = data['cpu']
    if data.has_key('memory'):
        node.memory = data['memory']

    if data.has_key('disk'):
        disk_data = data['disk']
        if type(disk_data) != list:
            disk_data = list(disk_data)

        for disk_data in disks_data:
            if type(disk_data) == str:
                size = parse_size(disk_data) / 1048576
                node.disks.append(Disk(size))
            else:
                raise ConfigError, "Disk customization is unsupported"

    if data.has_key('network'):
        networks_data = data['network']
        if type(networks_data) != list:
            networks_data = list(networks_data)

        for network_data in networks_data:
            if type(network_data) == str:
                network = None
                for n in environment.networks:
                    if n.name == network_data:
                        network = n
                        break

                if network is None:
                    network = parse_network(environment, {'name': network_data})


    if data.has_key('boot'):
        boot_data = data['boot']
        if type(boot_data) != list:
            boot_data = list(boot_data)

        for boot in boot_data:
            if not boot in ['disk', 'network']:
                raise ConfigError, "Unknown boot option: %s" % boot
            node.boot.append(boot)
    else:
        if len(node.disks)      > 0: node.boot.append('disk')
        if len(node.interfaces) > 0: node.boot.append('network')

    for existing_node in environment.nodes:
        if existing_node.name == node.name:
            raise ConfigError, "Node with given name already exists: %s" % node.name

    environment.nodes.append(node)



SIZE_RE = re.compile('\d+\s*(|k|kb|m|mb|g|gb)')

def parse_size(s):
    m = SIZE_RE.match(s)
    if not m:
        raise ValueError, "Invalid size format: %s" % s

    value = int(m[1])
    units = m[2].lower()
    if   units in ['k', 'kb']: multiplier=1024
    elif untis in ['m', 'mb']: multiplier=1024**2
    elif units in ['g', 'gb']: multiplier=1024**3
    elif units in ['t', 'tb']: multiplier=1024**4
    elif units == '': multiplier=1
    else: raise ValueError, "Invalid size format: %s" % s

    return value * multiplier

