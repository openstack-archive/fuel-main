
from devops.main import *

def saved(args):
    c = getController()
    for saved_env in c.saved_environments:
        print(saved_env)

def resume(args):
    parser = argparse.ArgumentParser(prog='devops resume')
    parser.add_argument('environment')
    arguments = parser.parse_args(args)
    env = load(arguments.environment)
    import code
    code.InteractiveConsole(locals={'environment': env}).interact()

import sys
import argparse

parser = argparse.ArgumentParser(prog='devops')
parser.add_argument('command', choices=['saved', 'resume'])
parser.add_argument('command_args', nargs=argparse.REMAINDER)
arguments = parser.parse_args()

if arguments.command == 'saved':
    saved(arguments.command_args)
elif arguments.command == 'resume':
    resume(arguments.command_args)
else:
    help()
    sys.exit(1)

