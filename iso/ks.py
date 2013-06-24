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
    def __init__(self, config_filename, template_filename):
        with open(config_filename, "r") as f:
            self.config = yaml.load(f.read())

        self.env = Environment(
            loader=FileSystemLoader(
                os.path.dirname(os.path.abspath(template_filename))
            )
        )
        self.template = self.env.get_template(
            os.path.basename(os.path.abspath(template_filename))
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
        '-t', '--template', dest='template', action='store', type=str,
        help='kickstart template file', required=True
    )
    parser.add_argument(
        '-c', '--config', dest='config', action='store', type=str,
        help='yaml config file', required=True
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store', type=str,
        help='where to output templating result', default='-'
    )
    params, other_params = parser.parse_known_args()

    ks = KickstartFile(
        config_filename=params.config,
        template_filename=params.template
    )

    if params.output == '-':
        print ks.render()
    else:
        ks.render2file(params.output)
