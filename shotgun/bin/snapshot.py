import sys
import os
import logging

sys.path[:0] = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

from shotgun.manager import Manager
from shotgun.config import Config

logging.basicConfig(level=logging.DEBUG)

with open("snapshot.json", "r") as fo:
    config = Config(fo.read())


manager = Manager(config)
manager.snapshot()
