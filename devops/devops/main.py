import logging

from devops import yaml_config_loader
from devops.error import DevopsError
from devops.controller import Controller
from devops.driver.libvirt import Libvirt

__all__ = ['logger', 'getController', 'build', 'destroy', 'load', 'save']

logger = logging.getLogger('devops')

controller = Controller(Libvirt())

def getController():
    return controller

def build(environment):
    controller.build_environment(environment)

def destroy(environment):
    controller.destroy_environment(environment)

def load(source):
    source = str(source).strip()
    if source.find("\n") == -1:
        if not source in controller.saved_environments:
            raise DevopsError, "Environment '%s' does not exist" % source
        return controller.load_environment(source)

    return yaml_config_loader.load(source)

def save(environment):
    controller.save_environment(environment)

