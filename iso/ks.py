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


import os
import argparse
import yaml

from jinja2 import FileSystemLoader
from jinja2 import Environment


class KickstartFile(object):
    def __init__(self, template_file, config_file=None, config_data=None):
        self.config = {}

        if config_file:
            with open(config_file, "r") as f:
                self.config.update(yaml.safe_load(f.read()))

        if config_data:
            self.config.update(yaml.safe_load(config_data))

        self.env = Environment(
            loader=FileSystemLoader(
                os.path.dirname(os.path.abspath(template_file))
            )
        )
        self.template = self.env.get_template(
            os.path.basename(os.path.abspath(template_file))
        )

    def render(self):
        return self.template.render(self.config)

    def render2file(self, filename):
        with open(filename, "w") as f:
            f.write(self.render())

if __name__ == "__main__":

    description = """
    This script builds kickstart file to using jinja2 template system.
    """

    parser = argparse.ArgumentParser(epilog=description)
    parser.add_argument(
        '-t', '--template-file', dest='template_file', action='store',
        type=str, help='kickstart template file', required=True
    )
    parser.add_argument(
        '-c', '--config-file', dest='config_file', action='store', type=str,
        help='yaml config file', required=False, default=None
    )
    parser.add_argument(
        '-u', '--config-data', dest='config_data', action='store', type=str,
        help='yaml config input', default='{}'
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store', type=str,
        help='where to output templating result', default='-'
    )
    params, other_params = parser.parse_known_args()

    ks = KickstartFile(
        template_file=params.template_file,
        config_file=params.config_file,
        config_data=params.config_data
    )

    if params.output == '-':
        print ks.render()
    else:
        ks.render2file(params.output)
