import os

LOGFILE = "/var/log/nailgun.log"
LOGLEVEL = "DEBUG"
PATH_TO_SSH_KEY = os.path.join(os.getenv("HOME"), ".ssh/id_rsa")
