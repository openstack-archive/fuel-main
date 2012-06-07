import os.path
import os
import sys

paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devops'),
]

sys.path[:0] = paths

import nose
import nose.config
import integration

integration.ci.set_iso('/var/www/nailgun-ubuntu-12.04-amd64.last.iso')

nc = nose.config.Config()
nc.verbosity = 3
nose.run(module=integration, config=nc)

