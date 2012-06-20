import yaml
import ipaddr

def ipv4_address_constructor(loader, node):
    return loader.make_python_instance('ipaddr.IPv4Address', node, args=[node.value])

def ipv4_network_constructor(loader, node):
    return loader.make_python_instance('ipaddr.IPv4Network', node, args=[node.value])

def python_object_string_representer(dumper, data):
    full_class_name = data.__class__.__name__
    if data.__module__:
        full_class_name = data.__module__ + '.' + full_class_name
    return yaml.ScalarNode("tag:yaml.org,2002:python/object:%s" % full_class_name, str(data), style=None)

class Loader(yaml.Loader):
    pass

class Dumper(yaml.Dumper):
    pass

Loader.add_constructor('tag:yaml.org,2002:python/object:ipaddr.IPv4Address', ipv4_address_constructor)
Loader.add_constructor('tag:yaml.org,2002:python/object:ipaddr.IPv4Network', ipv4_network_constructor)
Dumper.add_representer(ipaddr.IPv4Address, python_object_string_representer)
Dumper.add_representer(ipaddr.IPv4Network, python_object_string_representer)

def load(stream):
    return yaml.load(stream, Loader=Loader)

def dump(data):
    return yaml.dump(data, Dumper=Dumper)

