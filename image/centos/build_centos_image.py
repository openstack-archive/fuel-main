# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import imgcreate
from imgcreate.kickstart import FirewallConfig
# this monkey patch is for avoiding anaconda bug with firewall configuring
FirewallConfig.apply = lambda x, y: None


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-k', '--kickstart', dest='kickstart', action='store', type=str,
        help='kickstart file', required=True
    )
    parser.add_argument(
        '-n', '--name', dest='name', action='store', type=str,
        help='image name', required=True
    )
    parser.add_argument(
        '-c', '--cache', dest='cache', action='store', type=str,
        help='cache directory'
    )
    parser.add_argument(
        '-t', '--tmp', dest='tmp', action='store', type=str,
        help='tmp directory'
    )
    parser.add_argument(
        '-e', '--export', dest='export', action='store_true',
        help='export kernel and miniroot out of image', default=True
    )
    return parser


def main():

    imgcreate.setup_logging()
    parser = parse_args()
    params, other_params = parser.parse_known_args()

    kickstart = params.kickstart
    name = params.name



if __name__ == '__main__':
    main()