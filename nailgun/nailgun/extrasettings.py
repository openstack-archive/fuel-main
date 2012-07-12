import os
import os.path

LOGPATH = "/var/log/nailgun"
LOGFILE = os.path.join(LOGPATH, "nailgun.log")
LOGLEVEL = "DEBUG"
CELERYLOGFILE = os.path.join(LOGPATH, "celery.log")
CELERYLOGLEVEL = "DEBUG"

PATH_TO_SSH_KEY = os.path.join(os.getenv("HOME"), ".ssh", "id_rsa")
PATH_TO_BOOTSTRAP_SSH_KEY = os.path.join(os.getenv("HOME"),
                                         ".ssh",
                                        "bootstrap.rsa")

COBBLER_URL = "http://localhost/cobbler_api"
COBBLER_USER = "cobbler"
COBBLER_PASSWORD = "cobbler"
COBBLER_PROFILE = "centos-6.2-x86_64"
