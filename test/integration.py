import os.path
import sys
import pprint
pp = pprint.PrettyPrinter(indent=4)

paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devops'),
]

sys.path[:0] = paths

import nose
import nose.config
import integration

nc = nose.config.Config()
nc.verbosity = 3
nose.run(module=integration, config=nc)

