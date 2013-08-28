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
import json
import urllib2

API_ROOT = "http://127.0.0.1:8000/api/"


def format_table(data, **kwargs):
    rows = [tuple(x.values()) for x in data]

    header = tuple(data[0].keys())
    number_of_columns = len(header)
    column_widths = dict(
        zip(
            range(number_of_columns),
            (len(str(x)) for x in header)
        )
    )

    for row in rows:
        column_widths.update(
            (index, max(column_widths[index], len(str(element))))
            for index, element in enumerate(row)
        )
    row_template = ' | '.join(
        '%%-%ss' % column_widths[i] for i in range(number_of_columns)
    )

    return '\n'.join(
        (row_template % header,
         '-|-'.join(column_widths[column_index]*'-'
                    for column_index in range(number_of_columns)),
         '\n'.join(row_template % x for x in rows))
    )


def json_api_get_request(api):
    request = urllib2.urlopen(API_ROOT + api)
    return json.loads(request.read())


def release(params):
    if params.list:
        data = json_api_get_request("releases/")
        print(format_table(data))
    if params.rid:
        try:
            data = json_api_get_request("releases/" + params.rid + "/")
            print(format_table([data]))
        except urllib2.HTTPError:
            print("Error. No release with such rid!")
    print(params)


def environment(params):
    param_values = params.__dict__.values()
    param_values.remove("environment")
    if not any(param_values) or params.list:
        data = json_api_get_request("clusters/")
        print(data)
        # print format_table(data)


def node(params):
    print(params)


def network(params):
    print(params)


def settings(params):
    print(params)


def logs(params):
    print(params)


def task(params):
    print(params)


def notifications(params):
    print(params)


def health(params):
    print(params)


def deploy(params):
    print(params)


actions = {
    "release": {
        "action": release,
        "args": [{
            "args": ["-l", "--list"],
            "params": {
                "dest": "list",
                "action": "store_true",
                "help": "List all available releases.",
                "default": False
            }
        }, {
            "args": ["-c", "--config"],
            "params": {
                "dest": "config",
                "action": "store_true",
                "help": "Configure release with --rid",
                "default": False
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
                "action": "store_true",
                "help": "List all available environments.",
                "default": False
            }
        }, {
            "args": ["--create"],
            "params": {
                "dest": "create",
                "action": "store_true",
                "help": "Create a new environment with specific eid and name.",
                "default": False
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
                "action": "store_true",
                "help": "Rename environment with specific eid or ename",
                "default": False
            }
        }, {
            "args": ["-d", "--delete", "--environment-delete"],
            "params": {
                "dest": "delete",
                "action": "store_true",
                "help": "Delete environment with specific eid or ename",
                "default": False
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
                "action": "store_true",
                "help": "List all nodes.",
                "default": False
            }
        }, {
            "args": ["--alloc"],
            "params": {
                "dest": "alloc",
                "action": "store_true",
                "help": "List only allocated nodes.",
                "default": False
            }
        }, {
            "args": ["-s", "--set"],
            "params": {
                "dest": "set",
                "action": "store_true",
                "help": "Set role for specific node.",
                "default": False
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
                "action": "store_true",
                "help": "Remove node with specific nid.",
                "default": False
            }
        }]
    },
    "network": {
        "action": network,
        "args": [{
            "args": ["-d", "--default"],
            "params": {
                "dest": "default",
                "action": "store_true",
                "help": "Open default configuration.",
                "default": False
            }
        }, {
            "args": ["-m", "--modify"],
            "params": {
                "dest": "modify",
                "action": "store_true",
                "help": "Modify current configuration.",
                "default": False
            }
        }, {
            "args": ["-v", "--verify"],
            "params": {
                "dest": "verify",
                "action": "store_true",
                "help": "Verify current configuration.",
                "default": False
            }
        }, {
            "args": ["-c", "--cancel"],
            "params": {
                "dest": "cancel",
                "action": "store_true",
                "help": "Remove current changes in configuration.",
                "default": False
            }
        }, {
            "args": ["-s", "--save"],
            "params": {
                "dest": "save",
                "action": "store_true",
                "help": "Save current changes in configuration.",
                "default": False
            }
        }]
    },
    "settings": {
        "action": settings,
        "args": [{
            "args": ["-d", "--default"],
            "params": {
                "dest": "default",
                "action": "store_true",
                "help": "Open default configuration.",
                "default": False
            }
        }, {
            "args": ["-m", "--modify"],
            "params": {
                "dest": "modify",
                "action": "store_true",
                "help": "Modify current configuration.",
                "default": False
            }
        }, {
            "args": ["-c", "--cancel"],
            "params": {
                "dest": "cancel",
                "action": "store_true",
                "help": "Remove current changes in configuration.",
                "default": False
            }
        }, {
            "args": ["-s", "--save"],
            "params": {
                "dest": "save",
                "action": "store_true",
                "help": "Save current changes in configuration.",
                "default": False
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
                "help": "Service to use as log source. "
                        "(web backend, REST, orchestrator)",
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

    if params.action not in actions:
        parser.print_help()
        sys.exit(0)

    actions[params.action]["action"](params)
