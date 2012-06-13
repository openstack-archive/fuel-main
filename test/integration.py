import os.path
import os
import sys

import logging

logging.basicConfig(level=logging.DEBUG)

paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devops'),
]

sys.path[:0] = paths

import nose
import nose.config
import integration

iso = os.environ.get('NAILGUN_ISO', '/var/www/nailgun-ubuntu-12.04-amd64.last.iso')
ci = integration.Ci()
ci.teardown = lambda:None
ci.iso = iso
ci.env()
#ci.destroy()
integration.ci = ci


nc = nose.config.Config()
nc.verbosity = 3
nose.run(module=integration, config=nc)

