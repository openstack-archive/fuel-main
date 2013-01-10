import yaml
import cStringIO
import os.path
import logging
import logging.config

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

LOGGING = """
[loggers]
keys=root

[logger_root]
level=DEBUG
handlers={handlers}

[formatters]
keys=verbose

[formatter_verbose]
format=%(asctime)s %(levelname)s (%(module)s) %(message)s

[handlers]
keys=file,stream

[handler_file]
level=DEBUG
class=logging.handlers.WatchedFileHandler
args=("{logfile}",)
formatter=verbose

[handler_stream]
level=DEBUG
class=logging.StreamHandler
formatter=verbose
args=(sys.stdout,)
"""

LOGGING_HANDLER = 'file' if not int(settings.DEVELOPMENT) else 'stream'

if int(settings.DEVELOPMENT):
    logging.info("DEVELOPMENT MODE ON:")
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    settings.update({
        'STATIC_DIR': os.path.join(here, 'static'),
        'TEMPLATE_DIR': os.path.join(here, 'static')
    })
    logging.info("Static dir is %s" % settings.STATIC_DIR)
    logging.info("Template dir is %s" % settings.TEMPLATE_DIR)


logging.config.fileConfig(
    cStringIO.StringIO(
        LOGGING.format(
            logfile=settings.CUSTOM_LOG,
            handlers=LOGGING_HANDLER
        )
    )
)
