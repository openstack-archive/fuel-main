import sys
import os
import logging
import json

sys.path[:0] = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

from shotgun.manager import Manager
from shotgun.config import Config

logging.basicConfig(level=logging.DEBUG)

with open("snapshot.json", "r") as fo:
    data = json.loads(fo.read())
    config = Config(data)


manager = Manager(config)
manager.snapshot()
