import sys
import os

sys.path[:0] = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

from shotgun.driver import Driver
from shotgun.config import Config

with open("snapshot.json", "r") as fo:
    config = Config(fo.read())

data = list(config.objects)[0]
driver = Driver(data, config)

out = driver.command("ls -l /tmp | grep -v tmp")
print "return_code: %s" % out.return_code
print "out: %s" % out.stdout
print "err: %s" % out.stderr


