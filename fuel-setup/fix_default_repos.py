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
import os

import six
import yaml

from fuelclient import objects


FUELMENU_DEFAULT_SETTINGS_PATH = \
    "/usr/lib/python2.7/site-packages/fuelmenu/settings.yaml"


def is_subdict(dict1, dict2):
    """Checks that dict1 is subdict of dict2.

    >>> is_subdict({"a": 1}, {'a': 1, 'b': 1})
    True

    :param dict1: the candidate
    :param dict2: the super dict
    :return: True if all keys from dict1 are present
             and has same value in dict2 otherwise False
    """
    for k, v in six.iteritems(dict1):
        if k not in dict2 or dict2[k] != v:
            return False
    return True


def lists_merge(main, patch, key):
    """Merges the list of dicts with same keys.

    >>> lists_merge([{"a": 1, "c": 2}], [{"a": 1, "c": 3}], key="a")
    [{'a': 1, 'c': 3}]

    :param main: the main list
    :type main: list
    :param patch: the list of additional elements
    :type patch: list
    :param key: the key for compare
    """
    main_idx = dict(
        (x[key], i) for i, x in enumerate(main)
    )

    patch_idx = dict(
        (x[key], i) for i, x in enumerate(patch)
    )

    for k in sorted(patch_idx):
        if k in main_idx:
            main[main_idx[k]].update(patch[patch_idx[k]])
        else:
            main.append(patch[patch_idx[k]])
    return main


def update_release_repos(repositories,
                         release_match,
                         replace_repos=False):
    """Applies repositories for existing default settings.
    :param repositories: the meta information of repositories
    :param release_match: The pattern to check Fuel Release
    """
    releases = six.moves.filter(
        lambda x: is_subdict(release_match, x.data),
        objects.Release.get_all()
    )
    for release in releases:
        modified = _update_repository_settings(
            release.data["attributes_metadata"],
            repositories,
            replace_repos=replace_repos)
        if modified:
            release.data["attributes_metadata"] = modified
            print "Try to update the Release '%s'" % release.data['name']
            release.connection.put_request(
                release.instance_api_path.format(release.id),
                release.data
            )


def _update_repository_settings(settings,
                                repositories,
                                replace_repos=False):
    """Updates repository settings.
    :param settings: the target settings
    :param repositories: the meta of repositories
    """
    editable = settings["editable"]
    if 'repo_setup' not in editable:
        return

    repos_attr = editable["repo_setup"]["repos"]
    if replace_repos:
        repos_attr['value'] = repositories
    else:
        lists_merge(repos_attr['value'], repositories, "name")

    settings["editable"]["repo_setup"]["repos"] = repos_attr

    return settings


def fix_fuel_repos(address, port, user, password,
                   release_version, release_os, repositories):
    os.environ["SERVER_ADDRESS"] = address
    os.environ["LISTEN_PORT"] = port
    os.environ["KEYSTONE_USER"] = user
    os.environ["KEYSTONE_PASS"] = password

    release_match = {
        "version": release_version,
        "operating_system": release_os
    }

    update_release_repos(repositories, release_match)


def fix_fuelmenu_repos(repositories, replace_repos=False):
    print "Try to update default fuelmenu settings"
    with open(FUELMENU_DEFAULT_SETTINGS_PATH) as f:
        settings = yaml.safe_load(f)
    if replace_repos:
        settings["BOOTSTRAP"]["repos"] = repositories
    else:
        lists_merge(settings["BOOTSTRAP"]["repos"], repositories, "name")
    with open(FUELMENU_DEFAULT_SETTINGS_PATH, "w") as f:
        f.write(yaml.safe_dump(settings, default_flow_style=False))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="action", help='actions'
    )
    fuel_parser = subparsers.add_parser(
        'fuel', help='fix fuel repos'
    )
    fuel_parser.add_argument(
        '--release-version', dest='release_version', action='store',
        type=str, help='release version', default='newton-10.0'
    )
    fuel_parser.add_argument(
        '--release-os', dest='release_os', action='store',
        type=str, help='release operating system', default='Ubuntu'
    )
    fuel_parser.add_argument(
        '--repositories-file', dest='repositories_file', action='store',
        type=str, help='file where repositories are defined', required=True
    )
    fuel_parser.add_argument(
        '-a', '--address', dest='address', action='store', type=str,
        help='fuel address', default='127.0.0.1'
    )
    fuel_parser.add_argument(
        '-p', '--port', dest='port', action='store', type=str,
        help='fuel port', default='8000'
    )
    fuel_parser.add_argument(
        '--user', dest='user', action='store', type=str,
        help='fuel user', default='admin'
    )
    fuel_parser.add_argument(
        '--password', dest='password', action='store', type=str,
        help='fuel password', default='admin'
    )
    fuelmenu_parser = subparsers.add_parser(
        'fuelmenu', help='fix fuelmenu repos'
    )
    fuelmenu_parser.add_argument(
        '--repositories-file', dest='repositories_file', action='store',
        type=str, help='file where repositories are defined', required=True
    )
    params, other_params = parser.parse_known_args()

    with open(params.repositories_file) as f:
        repositories = yaml.safe_load(f)

    if params.action == 'fuel':
        fix_fuel_repos(params.address, params.port,
                       params.user, params.password,
                       params.release_version, params.release_os,
                       repositories)
    else:
        fix_fuelmenu_repos(repositories)


if __name__ == "__main__":
    main()
