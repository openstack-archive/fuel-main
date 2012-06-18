import os.path
import os
import sys
import logging
import argparse

paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devops'),
]
sys.path[:0] = paths

import nose
import nose.config
import integration

logger = logging.getLogger('integration')

def prepare(ci, destroy_after=False, iso=None):

    if not destroy_after:
        ci.tearDown = lambda:None

    if iso:
        ci.iso = iso


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Integration test suite")
    parser.add_argument("-i", "--iso", dest="iso",
                      help="iso image path or http://url", required=True)
    parser.add_argument("-l", "--level", dest="log_level", type=str,
                      help="log level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      default="ERROR", metavar="LEVEL")
    parser.add_argument("-d", "--destroy-after", dest="destroy_after", action="store_true",
                      help="destroy environment after testing", default=False)
    parser.add_argument("-c", "--destroy-before", dest="destroy_before", action="store_true",
                      help="destroy environment before testing", default=False)
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true",
                      help="do not run real testing", default=False)

    namespace = parser.parse_args()

    numeric_level = getattr(logging, namespace.log_level.upper())
    logging.basicConfig(level=numeric_level)

    for o, v in namespace._get_kwargs():
        logger.debug("Parsed option: %s = %s" % (o, v))

    ci = integration.Ci()

    if namespace.destroy_before:
        ci.destroy()

    if not namespace.dry_run:
        logger.debug("Preparing for real testing")
        prepare(ci, destroy_after=namespace.destroy_after, iso=namespace.iso)

        integration.ci = ci

        nc = nose.config.Config()
        nc.verbosity = 3
        nose.main(module=integration, config=nc, argv=[__file__])
