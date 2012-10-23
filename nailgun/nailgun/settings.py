import yaml
import os.path
import logging

from pkg_resources import resource_filename


class NailgunSettings:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        settings_files = []
        self.logger.debug("Looking for settings.yaml package config "
                          "using old style __file__")
        project_path = os.path.dirname(__file__)
        project_settings_file = os.path.join(project_path, 'settings.yaml')
        settings_files.append(project_settings_file)

        settings_files.append('/etc/nailgun/settings.yaml')
        self.config = {}

        for sf in settings_files:
            try:
                self.logger.debug("Trying to read config file %s" % sf)
                with open(sf, 'r') as f:
                    self.config.update(yaml.load(f.read()))
            except Exception as e:
                self.logger.debug("Error while reading config file %s: %s" %
                                  (sf, str(e)))

    def update(self, dct):
        self.config.update(dct)

    def __getattr__(self, name):
        return self.config.get(name, None)


settings = NailgunSettings()

if int(settings.DEVELOPMENT):
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    settings.update({
        'STATIC_DIR': os.path.join(here, 'static'),
        'TEMPLATE_DIR': os.path.join(here, 'static'),
        'LOGFILE': os.path.join(here, 'nailgun.log'),
        'DATABASE_ENGINE': 'sqlite:///%s' %
        os.path.join(here, 'nailgun.sqlite')})
