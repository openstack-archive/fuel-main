import logging
from error import DevopsError
from controller import Controller
from driver.libvirt import Libvirt
import yaml_config_loader

__all__ = ['logger', 'getController', 'build', 'destroy', 'load', 'save']

logger = logging.getLogger('devops')


class ControllerSingleton(Controller):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ControllerSingleton, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance


def getController():
    return ControllerSingleton(Libvirt())


def build(environment):
    getController().build_environment(environment)


def destroy(environment):
    getController().destroy_environment(environment)


def load(source):
    source = str(source).strip()
    if source.find("\n") == -1:
        if not source in getController().saved_environments:
            raise DevopsError, "Environment '%s' does not exist" % source
        return getController().load_environment(source)

    return yaml_config_loader.load(source)


def save(environment):
    getController().save_environment(environment)
