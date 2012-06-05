
from devops import yaml_config_loader
from devops.controller import Controller
from devops.driver.libvirt import Libvirt

__all__ = ['build', 'destroy', 'load']

controller = Controller(Libvirt())

def build(environment):
    controller.build_environment(environment)

def destroy(environment):
    controller.destroy_environment(environment)

def load(source):
    return yaml_config_loader.load(source)

