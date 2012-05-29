
import time

from devops.model import Environment, Node, Network, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt

from devops import yaml_config_loader

env = yaml_config_loader.load("""
name: 'Sample environment'
networks:
  - network: internal
  - network: external
    type: bridged
nodes:
  - node: gateway
    disk: '5Gb'
    networks: ['external', 'internal']
  - node: slug
    networks: ['internal']
""")

# e = Environment('sample')
# 
# network = Network('net1')
# node = Node('foo')
# node.interfaces.append(Interface(network))
# 
# e.networks.append(network)
# e.nodes.append(node)

controller = Controller(Libvirt())
controller.build_environment(env)

print("Environment created")

env.node['gateway'].start()

print("Node started")

print("Sleeping 5 seconds")
time.sleep(5)

controller.destroy_environment(env)

print("Environment destroyed")

