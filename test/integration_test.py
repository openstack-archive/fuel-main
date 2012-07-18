import os.path
import os
import sys
import logging
import argparse
from nose.plugins.xunit import Xunit
from nose.plugins.manager import PluginManager

paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devops'),
]
sys.path[:0] = paths

import cookbooks
import integration

logger = logging.getLogger('integration')

def main():
    parser = argparse.ArgumentParser(description="Integration test suite")
    parser.add_argument("-i", "--iso", dest="iso",
                      help="iso image path or http://url")
    parser.add_argument("-l", "--level", dest="log_level", type=str,
                      help="log level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      default="ERROR", metavar="LEVEL")
    parser.add_argument('--cache-file', dest='cache_file', type=str,
                      help='file to store integration environment name')
    parser.add_argument('--installation-timeout', dest='installation_timeout', type=int,
                      help='admin node installation timeout')
    parser.add_argument('--chef-timeout', dest='chef_timeout', type=int,
                      help='admin node chef timeout')
    parser.add_argument('--suite', dest='test_suite', type=str,
                      help='Test suite to run', choices=["integration", "cookbooks"],
                      default="integration")
    parser.add_argument('command', choices=('setup', 'destroy', 'test'), default='test',
                      help="command to execute")

    params = parser.parse_args()

    numeric_level = getattr(logging, params.log_level.upper())
    logging.basicConfig(level=numeric_level)

    if params.test_suite == 'integration':
        suite = integration
    elif params.test_suite == 'cookbooks':
        suite = cookbooks

    suite.ci = suite.Ci(cache_file=params.cache_file, iso=params.iso)
    suite.ci.installation_timeout = getattr(params, 'installation_timeout', 1800)
    suite.ci.chef_timeout = getattr(params, 'chef_timeout', 600)

    if params.command == 'setup':
        result = suite.ci.setup_environment()
    elif params.command == 'destroy':
        result = suite.ci.destroy_environment()
    elif params.command == 'test':
        import nose
        import nose.config

        nc = nose.config.Config()
        nc.verbosity = 3
        nc.plugins = PluginManager(plugins=[Xunit()])
        # Set folder where to process tests
        nc.configureWhere(os.path.join(os.path.dirname(os.path.abspath(__file__)), params.test_suite))
        nose.main(module=suite, config=nc, argv=[
            __file__,
            "--with-xunit",
            "--xunit-file=test/nosetests.xml"
        ])
        result = True
    else:
        print("Unknown command '%s'" % params.command)
        sys.exit(1)

    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()

