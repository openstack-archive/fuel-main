#!/usr/bin/env python
#    Copyright 2016 Mirantis, Inc.
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
import yaml


def generate_yum_repos_config(repositories):
    config = ""
    for repo in repositories:
        config += """
[{name}]
name={name}
baseurl={uri}
enabled=1
gpgcheck=0
priority={priority}
skip_if_unavailable=1
""".format(**repo)
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--repositories-file', dest='repositories_file', action='store',
        type=str, help='file where repositories are defined', required=True
    )
    parser.add_argument(
        '--output-file', dest='outfile', action='store',
        type=str, help='file where to write yum config', required=True
    )
    params, other_params = parser.parse_known_args()

    with open(params.repositories_file) as f:
        repositories = yaml.safe_load(f)

    with open(params.outfile, 'wt') as f:
        f.write(generate_yum_repos_config(repositories))


if __name__ == "__main__":
    main()
