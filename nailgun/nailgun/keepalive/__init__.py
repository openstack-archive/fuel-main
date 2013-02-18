from watcher import KeepAliveThread
from nailgun.db import orm
from nailgun.api.models import Node

keep_alive = KeepAliveThread()
