import sys
import cStringIO
import os.path
import logging
import logging.config

import yaml

from pkg_resources import resource_filename


class NailgunSettings(object):
    def __init__(self):
        logger = logging.getLogger("nailgun")
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s (%(module)s) %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        settings_files = []
        logger.debug("Looking for settings.yaml package config "
                     "using old style __file__")
        project_path = os.path.dirname(__file__)
        project_settings_file = os.path.join(project_path, 'settings.yaml')
        settings_files.append(project_settings_file)

        settings_files.append('/etc/nailgun/settings.yaml')
        settings_files.append('/etc/nailgun/version.yaml')
        self.config = {}

        for sf in settings_files:
            try:
                logger.debug("Trying to read config file %s" % sf)
                self.update_from_file(sf)
            except Exception as e:
                logger.debug("Error while reading config file %s: %s" %
                             (sf, str(e)))

        if not int(self.config.get("DEVELOPMENT")):
            logger.removeHandler(handler)
            handler = logging.handlers.WatchedFileHandler(
                self.config.get("CUSTOM_LOG")
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            logger.info("DEVELOPMENT MODE ON:")
            here = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')
            )
            self.config.update({
                'STATIC_DIR': os.path.join(here, 'static'),
                'TEMPLATE_DIR': os.path.join(here, 'static')
            })
            logger.info("Static dir is %s" % self.config.get("STATIC_DIR"))
            logger.info("Template dir is %s" % self.config.get("TEMPLATE_DIR"))

    def update(self, dct):
        self.config.update(dct)

    def update_from_file(self, path):
        with open(path, "r") as custom_config:
            self.config.update(
                yaml.load(custom_config.read())
            )

    def dump(self):
        return yaml.dump(self.config)

    def __getattr__(self, name):
        return self.config.get(name, None)

    def __repr__(self):
        return "<settings object>"


settings = NailgunSettings()
