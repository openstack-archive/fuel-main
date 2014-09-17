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

import yaml


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--filename', dest='image_filename', action='store',
        type=str, required=True)
    parser.add_argument(
        '--container', dest='image_container', action='store',
        type=str, required=False, default="gzip")
    parser.add_argument(
        '--format', dest='image_format', action='store',
        type=str, required=True)
    parser.add_argument(
        '--mountpoint', dest='image_mountpoint', action='store',
        type=str, required=True)
    parser.add_argument(
        '-O', '--output-file', dest='output_file', action='store',
        type=str, required=False, default="profile.yaml",
        help='Output file',
    )

    return parser


def main():
    parser = parse_args()
    params, other_params = parser.parse_known_args()

    data = []

    try:
        with open(params.output_file) as f:
            data = yaml.load(f.read()) or []
    except:
        pass

    data.append({params.image_mountpoint: {
        'filename': params.image_filename,
        'container': params.image_container,
        'format': params.image_format}})

    with open(params.output_file, 'wb') as f:
        f.write(yaml.dump(data))


if __name__ == '__main__':
    main()
