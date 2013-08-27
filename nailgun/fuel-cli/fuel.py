#!/usr/bin/env python
#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse


def release(params):
    print params


def environment(params):
    print params


def node(params):
    print params


def network(params):
    print params


def settings(params):
    print params


def logs(params):
    print params


def task(params):
    print params


def notifications(params):
    print params


def health(params):
    print params


def deploy(params):
    print params


actions = {
    "release": {
        "action": release,
        "args": [{
            "args": ["-l", "--list"],
            "params": {
                "dest": "list",
                "action": "store",
                "type": str,
                "help": "List all available releases.",
                "default": None
            }
        }, {
            "args": ["-c", "--config"],
            "params": {
                "dest": "config",
                "action": "store",
                "type": str,
                "help": "Configure release with --rid",
                "default": None
            }
        }, {
            "args": ["--rid"],
            "params": {
                "dest": "rid",
                "action": "store",
                "type": str,
                "help": "Specify release id to configure",
                "default": None
            }
        }]
    },
    "environment": {
        "action": environment,
        "args": [{
            "args": ["-l", "--list"],
            "params": {
                "dest": "list",
                "action": "store",
                "type": str,
                "help": "List all available environments.",
                "default": None
            }
        }, {
            "args": ["--create"],
            "params": {
                "dest": "create",
                "action": "store",
                "type": str,
                "help": "Create a new environment with specific eid and name.",
                "default": None
            }
        }, {
            "args": ["--eid", "--environment-id"],
            "params": {
                "dest": "eid",
                "action": "store",
                "type": str,
                "help": "environment id",
                "default": None
            }
        }, {
            "args": ["--ename", "--environment-name"],
            "params": {
                "dest": "ename",
                "action": "store",
                "type": str,
                "help": "environment name",
                "default": None
            }
        }, {
            "args": ["--rename", "--environment-rename"],
            "params": {
                "dest": "rename",
                "action": "store",
                "type": str,
                "help": "Rename environment with specific eid or ename",
                "default": None
            }
        }, {
            "args": ["-d", "--delete", "--environment-delete"],
            "params": {
                "dest": "delete",
                "action": "store",
                "type": str,
                "help": "Delete environment with specific eid or ename",
                "default": None
            }
        }, {
            "args": ["--nname", "--new-name"],
            "params": {
                "dest": "nname",
                "action": "store",
                "type": str,
                "help": "New name for environment with specific eid or ename",
                "default": None
            }
        }]
    },
    "node": {
        "action": node,
        "args": [{
            "args": ["-l", "--list"],
            "params": {
                "dest": "list",
                "action": "store",
                "type": str,
                "help": "List all nodes.",
                "default": None
            }
        }, {
            "args": ["--alloc"],
            "params": {
                "dest": "alloc",
                "action": "store",
                "type": str,
                "help": "List only allocated nodes.",
                "default": None
            }
        }, {
            "args": ["-s", "--set"],
            "params": {
                "dest": "set",
                "action": "store",
                "type": str,
                "help": "Set role for specific node.",
                "default": None
            }
        }, {
            "args": ["--nid", "--node-id"],
            "params": {
                "dest": "nid",
                "action": "store",
                "type": str,
                "help": "Node id.",
                "default": None
            }
        }, {
            "args": ["-r", "--role"],
            "params": {
                "dest": "role",
                "action": "store",
                "type": str,
                "help": "Role to assign for node with nid.",
                "default": None
            }
        }, {
            "args": ["-rm", "--remove"],
            "params": {
                "dest": "remove",
                "action": "store",
                "type": str,
                "help": "Remove node with specific nid.",
                "default": None
            }
        }]
    },
    "network": {
        "action": network,
        "args": [{
            "args": ["-d", "--default"],
            "params": {
                "dest": "default",
                "action": "store",
                "type": str,
                "help": "Open default configuration.",
                "default": None
            }
        }, {
            "args": ["-m", "--modify"],
            "params": {
                "dest": "modify",
                "action": "store",
                "type": str,
                "help": "Modify current configuration.",
                "default": None
            }
        }, {
            "args": ["-v", "--verify"],
            "params": {
                "dest": "verify",
                "action": "store",
                "type": str,
                "help": "Verify current configuration.",
                "default": None
            }
        }, {
            "args": ["-c", "--cancel"],
            "params": {
                "dest": "cancel",
                "action": "store",
                "type": str,
                "help": "Remove current changes in configuration.",
                "default": None
            }
        }, {
            "args": ["-s", "--save"],
            "params": {
                "dest": "save",
                "action": "store",
                "type": str,
                "help": "Save current changes in configuration.",
                "default": None
            }
        }]
    },
    "settings": {
        "action": settings,
        "args": [{
            "args": ["-d", "--default"],
            "params": {
                "dest": "default",
                "action": "store",
                "type": str,
                "help": "Open default configuration.",
                "default": None
            }
        }, {
            "args": ["-m", "--modify"],
            "params": {
                "dest": "modify",
                "action": "store",
                "type": str,
                "help": "Modify current configuration.",
                "default": None
            }
        }, {
            "args": ["-c", "--cancel"],
            "params": {
                "dest": "cancel",
                "action": "store",
                "type": str,
                "help": "Remove current changes in configuration.",
                "default": None
            }
        }, {
            "args": ["-s", "--save"],
            "params": {
                "dest": "save",
                "action": "store",
                "type": str,
                "help": "Save current changes in configuration.",
                "default": None
            }
        }]
    },
    "logs": {
        "action": logs,
        "args": [{
            "args": ["-db", "--date-before"],
            "params": {
                "dest": "before",
                "action": "store",
                "type": str,
                "help": "Date before which collect logs.",
                "default": None
            }
        }, {
            "args": ["-da", "--date-after"],
            "params": {
                "dest": "after",
                "action": "store",
                "type": str,
                "help": "Date after which collect logs.",
                "default": None
            }
        }, {
            "args": ["-m", "--max-entries"],
            "params": {
                "dest": "max",
                "action": "store",
                "type": str,
                "help": "Maximum number of log entries.",
                "default": None
            }
        }, {
            "args": ["-n", "--node"],
            "params": {
                "dest": "node",
                "action": "store",
                "type": str,
                "help": "From which node to collect logs.",
                "default": None
            }
        }, {
            "args": ["-s", "--source"],
            "params": {
                "dest": "source",
                "action": "store",
                "type": str,
                "help": "Service to use as log source. e.g. `web backend`, REST, orchestrator",
                "default": None
            }
        }, {
            "args": ["-ll", "--log-level"],
            "params": {
                "dest": "level",
                "action": "store",
                "type": str,
                "help": "Log level. e.g DEBUG, INFO, WARNING",
                "default": None
            }
        }]
    },
    "task": {
        "action": task,
        "args": []
    },
    "notification": {
        "action": notifications,
        "args": []
    },
    "health": {
        "action": health,
        "args": []
    },
    "deploy": {
        "action": deploy,
        "args": []
    }
}

import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="action", help='actions'
    )

    for action, params in actions.iteritems():
        action_parser = subparsers.add_parser(
            action, help=params["action"].__doc__
        )
        for arg in params.get("args", []):
            action_parser.add_argument(
                *arg["args"],
                **arg["params"]
            )

    params, other_params = parser.parse_known_args()
    sys.argv.pop(1)

    if not params.action in actions:
        parser.print_help()
        sys.exit(0)

    actions[params.action]["action"](params)