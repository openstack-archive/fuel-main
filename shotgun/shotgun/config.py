import time

from shotgun import settings

class Config(object):
    def __init__(self, data=None):
        self.data = data
        self.time = time.localtime()

    def _timestamp(self, name):
        return "{0}-{1}".format(name,
            time.strftime('%Y-%m-%d_%H-%M-%S', self.time))

    @property
    def target(self):
        target = self.data.get("target", settings.TARGET)
        if self.data.get("timestamp", settings.TIMESTAMP):
            target = self._timestamp(target)
        return target

    @property
    def objects(self):
        for role, hosts in self.data["dump_roles"].iteritems():
            for host in hosts:
                for obj in self.data["dump_objects"].get(role, []):
                    obj["host"] = host
                    yield obj
