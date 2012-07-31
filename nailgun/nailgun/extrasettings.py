import os
import os.path

LOGPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGFILE = os.path.join(LOGPATH, "nailgun.log")
LOGLEVEL = "DEBUG"
CELERYLOGFILE = os.path.join(LOGPATH, "celery.log")
CELERYLOGLEVEL = "DEBUG"
CHEF_CONF_FOLDER = LOGPATH  # For testing purposes

PATH_TO_SSH_KEY = os.path.join(os.getenv("HOME"), ".ssh", "id_rsa")
PATH_TO_BOOTSTRAP_SSH_KEY = os.path.join(os.getenv("HOME"),
                                         ".ssh",
                                        "bootstrap.rsa")

COBBLER_URL = "http://localhost/cobbler_api"
COBBLER_USER = "cobbler"
COBBLER_PASSWORD = "cobbler"
COBBLER_PROFILE = "centos-6.2-x86_64"
