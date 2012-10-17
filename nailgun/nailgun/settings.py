import yaml
import os.path
import logging

from pkg_resources import resource_filename


class NailgunSettings:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        settings_files = []
        try:
            self.logger.debug("Looking for settings.yaml package config "
                              "using old style __file__")
            project_path = os.path.dirname(__file__)
            project_settings_file = os.path.join(project_path, 'settings.yaml')
        except:
            self.logger.error("Error while reading old style settings.yaml "
                              "package config")
        else:
            settings_files.append(project_settings_file)

        try:
            self.logger.debug("Looking for settings.yaml package config "
                              "using setuptools")
            local_settings_file = resource_filename(__name__, 'settings.yaml')
        except:
            self.logger.error("Error while finding old style settings.yaml "
                              "package config")
        else:
            settings_files.append(local_settings_file)

        settings_files.append('/etc/nailgun/settings.yaml')
        self.config = {}

        for sf in settings_files:
            try:
                self.logger.debug("Trying to read config file %s" % sf)
                with open(sf, 'r') as f:
                    self.config.update(yaml.load(f.read()))
            except Exception as e:
                self.logger.error("Error while reading config file %s: %s" %
                                  (sf, str(e)))

    def __getattr__(self, name):
        return self.config.get(name, None)


settings = NailgunSettings()
