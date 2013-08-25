import os
import logging

from shotgun.driver import Driver
from shotgun.utils import execute

logger = logging.getLogger()

class Manager(object):
    def __init__(self, conf):
        self.conf = conf

    def snapshot(self):
        for obj_data in self.conf.objects:
            driver = Driver.getDriver(obj_data, self.conf)
            driver.snapshot()
        logger.debug("Archiving dump directory: %s", self.conf.target)
        execute("tar zcf {0}.tgz -C {1} {2}"
                "".format(self.conf.target,
                          os.path.dirname(self.conf.target),
                          os.path.basename(self.conf.target)))


