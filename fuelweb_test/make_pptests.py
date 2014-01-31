"""
Script for creating Puppet integration tests scripts using template engine.
"""

import argparse
from puppet_tests.pp_testgenerator import PuppetTestGenerator

parser = argparse.ArgumentParser()
parser.add_argument("tests", type=str, help="Directory to save tests")
parser.add_argument("modules", type=str, help="Path to Puppet modules")
parser.add_argument("-k", "--keep_tests",
                    action='store_true',
                    help="Keep previous test files",
                    default=False)

args = parser.parse_args()
generator = PuppetTestGenerator(args.tests, args.modules)
if not args.keep_tests:
    generator.remove_all_tests()

generator.make_all_scripts()
