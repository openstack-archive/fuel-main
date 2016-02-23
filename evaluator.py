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
import os

from jinja2 import FileSystemLoader
from jinja2 import Environment
import yaml


def traverse(data, flat_dict, head='', depth=-1):

    if depth == 0 or isinstance(data, (unicode, str)):
        flat_dict[head] = data
    elif isinstance(data, dict):
        for key, value in data.iteritems():
            new_head = "{head}_{tail}".format(head=head, tail=key).lstrip('_')
            traverse(value, flat_dict, new_head, depth - 1)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_head = "{head}_{tail}".format(head=head, tail=i).lstrip('_')
            traverse(item, flat_dict, new_head, depth - 1)


class Evaluator(object):
    def __init__(self, template_file=None, config_file=None,
                 config_data=None, flat_prefix='', flat_depth=-1):
        self.template_file = template_file
        self.config = {}
        self.flat_config = {}
        self.flat_prefix = flat_prefix
        self.flat_depth = flat_depth

        if config_file:
            with open(config_file, "r") as f:
                self.config.update(
                    self._dictify(yaml.safe_load(f)))

        if config_data:
            self.config.update(
                self._dictify(yaml.safe_load(config_data)))

        traverse(self.config, self.flat_config, depth=self.flat_depth)

    def _dictify(self, data):
        if isinstance(data, list):
            return {k: v for k, v in enumerate(data)}
        return data

    def jinja2_render(self):
        if self.template_file is None:
            return ''
        env = Environment(
            loader=FileSystemLoader(
                os.path.dirname(os.path.abspath(self.template_file))
            )
        )
        template = env.get_template(
            os.path.basename(os.path.abspath(self.template_file))
        )
        return template.render(self.config)

    def make_render(self):
        return '\n'.join(
            ('{prefix}{0} ?= {1}'.format(k, v, prefix=self.flat_prefix)
             for k, v in sorted(self.flat_config.iteritems()))) + '\n'

    def render(self, render_type):
        return getattr(self, '{0}_render'.format(render_type))()


if __name__ == "__main__":

    description = """
    This script evaluates jinja2 template.
    """

    parser = argparse.ArgumentParser(epilog=description)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-t', '--template-file', dest='template_file', action='store',
        type=str, help='jinja2 template file'
    )
    group.add_argument(
        '-m', '--make', dest='make_output', action='store_true',
        help='output will be valid make', default=False
    )
    parser.add_argument(
        '-c', '--config-file', dest='config_file', action='store', type=str,
        help='yaml config file', default=None
    )
    parser.add_argument(
        '-u', '--config-data', dest='config_data', action='store', type=str,
        help='yaml config input', default=None
    )
    parser.add_argument(
        '-p', '--flat-prefix', dest='flat_prefix', action='store', type=str,
        help='prefix for flat dict keys', default=''
    )
    parser.add_argument(
        '-d', '--flat-depth', dest='flat_depth', action='store', type=int,
        help='depth for flat dict', default=-1
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store', type=str,
        help='where to output templating result', default='-'
    )
    params, other_params = parser.parse_known_args()

    evaluator = Evaluator(
        template_file=params.template_file or None,
        config_file=params.config_file,
        config_data=params.config_data,
        flat_prefix=params.flat_prefix,
        flat_depth=params.flat_depth,
    )

    if not params.template_file is None:
        render_type = 'jinja2'
    elif params.make_output:
        render_type = 'make'
    else:
        parser.print_help()
    if params.output == '-':
        print evaluator.render(render_type)
    else:
        with open(params.output, 'w') as f:
            f.write(evaluator.render(render_type))
