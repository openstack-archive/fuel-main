import os.path
import os
import sys
import logging
from optparse import OptionParser

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
    parser = OptionParser()
    parser.add_option("-i", "--iso", dest="iso",
                      help="iso image path or http://url", default=None)
    parser.add_option("-l", "--level", dest="log_level", type="choice",
                      help="log level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      default="ERROR", metavar="LEVEL")
    parser.add_option("-d", "--destroy-after", dest="destroy_after", action="store_true",
                      help="destroy environment after testing", default=False)
    parser.add_option("-c", "--destroy-before", dest="destroy_before", action="store_true",
                      help="destroy environment before testing", default=False)
    parser.add_option("-n", "--dry-run", dest="dry_run", action="store_true",
                      help="do not run real testing", default=False)

    (options, args) = parser.parse_args()
    optdict = options.__dict__
    print sys.argv

    numeric_level = getattr(logging, options.log_level.upper())
    logging.basicConfig(level=numeric_level)

    for o, v in optdict.items():
        logger.debug("Parsed option: %s = %s" % (o, v))

    ci = integration.Ci()

    if optdict["destroy_before"]:
        ci.destroy()

    if not optdict["dry_run"]:
        logger.debug("Preparing for real testing")
        prepare(ci, destroy_after=optdict["destroy_after"], iso=optdict["iso"])
        
        integration.ci = ci

        nc = nose.config.Config()
        nc.verbosity = 3
        nose.main(module=integration, config=nc, argv=[__file__])
