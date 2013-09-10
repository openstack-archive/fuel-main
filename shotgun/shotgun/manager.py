import os
import logging

from shotgun.logger import logger
from shotgun.driver import Driver
from shotgun.utils import execute


class Manager(object):
    def __init__(self, conf):
        logger.debug("Initializing snapshot manager")
        self.conf = conf

    def snapshot(self):
        logger.debug("Making snapshot")
        for obj_data in self.conf.objects:
            logger.debug("Dumping: %s", obj_data)
            driver = Driver.getDriver(obj_data, self.conf)
            driver.snapshot()
        logger.debug("Archiving dump directory: %s", self.conf.target)
        execute("tar zcf {0}.tgz -C {1} {2}"
                "".format(self.conf.target,
                          os.path.dirname(self.conf.target),
                          os.path.basename(self.conf.target)))
        execute("rm -r {0}".format(self.conf.target))
        with open(self.conf.lastdump, "w") as fo:
            fo.write("%s.tgz" % self.conf.target)
        return "%s.tgz" % self.conf.target
