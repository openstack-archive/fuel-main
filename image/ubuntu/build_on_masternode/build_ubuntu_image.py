#!/usr/bin/env python
# Copyright 2015 Mirantis, Inc.
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
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import urlparse

import yaml


TRUSTY_PACKAGES = [
    "bash-completion",
    "curl",
    "daemonize",
    "build-essential",
    "gdisk",
    "grub-pc",
    "linux-firmware",
    "linux-firmware-nonfree",
    "linux-image-generic-lts-trusty",
    "linux-headers-generic-lts-trusty",
    "lvm2",
    "mdadm",
    "nailgun-agent",
    "nailgun-mcagents",
    "nailgun-net-check",
    "ntp",
    "openssh-client",
    "openssh-server",
    "telnet",
    "ubuntu-minimal",
    "ubuntu-standard",
    "virt-what",
    "acl",
    "anacron",
    "bridge-utils",
    "bsdmainutils",
    "cloud-init",
    "debconf-utils",
    "ruby-augeas",
    "ruby-shadow",
    "ruby-json",
    "mcollective",
    "puppet",
    "python-amqp",
    "ruby-ipaddress",
    "ruby-netaddr",
    "ruby-openstack",
    "ruby-stomp",
    "vim",
    "vlan",
    "uuid-runtime",
]

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler(sys.stderr))


def execute(*cmd, **kwargs):
    command = ' '.join(cmd)
    LOG.debug('Trying to execute command: %s', command)
    commands = [c.strip() for c in re.split(ur'\|', command)]
    check_exit_code = kwargs.pop('check_exit_code', [0])
    ignore_exit_code = False
    to_filename = kwargs.get('to_filename')
    cwd = kwargs.get('cwd')

    if isinstance(check_exit_code, bool):
        ignore_exit_code = not check_exit_code
        check_exit_code = [0]
    elif isinstance(check_exit_code, int):
        check_exit_code = [check_exit_code]

    to_file = None
    if to_filename:
        to_file = open(to_filename, 'wb')

    process = []
    for c in commands:
        try:
            # NOTE(eli): Python's shlex implementation doesn't like unicode.
            # We have to convert to ascii before shlex'ing the command.
            # http://bugs.python.org/issue6988
            encoded_command = c.encode('ascii')

            process.append(subprocess.Popen(
                shlex.split(encoded_command),
                stdin=(process[-1].stdout if process else None),
                stdout=(to_file
                        if (len(process) == len(commands) - 1) and to_file
                        else subprocess.PIPE),
                stderr=(subprocess.PIPE),
                cwd=cwd
            ))
        except OSError as e:
            raise Exception("Couldn't execute cmd=%s, err=%s" % (command, e))
        if len(process) >= 2:
            process[-2].stdout.close()
    stdout, stderr = process[-1].communicate()
    return (stdout, stderr, process[-1].returncode)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_data", help='JSON encoded string')
    return parser


def expose_env_params(json_data=None):
    if not json_data:
        json_data = {}
    os.environ["UBUNTU_MAJOR"] = json_data.get('ubuntu_major', '12')
    os.environ["UBUNTU_MINOR"] = json_data.get('ubuntu_minor', '04')
    os.environ["UBUNTU_ARCH"] = json_data.get('ubuntu_arch', 'amd64')
    os.environ["UBUNTU_RELEASE"] = json_data.get('codename', 'precise')
    os.environ["UBUNTU_KERNEL_FLAVOR"] = json_data.get('ubuntu_kernel_flavor',
                                                       'lts-trusty')
    os.environ["DST_DIR"] = json_data.get('output', '/tmp/image')
    if 'image_data' in json_data:
        os.environ["SEPARATE_FS_IMAGES"] = " ".join(
            ["%s,%s" % (k, v['format'])
             for k, v in json_data['image_data'].items()])
        os.environ["SEPARATE_FS_IMAGES_NAMES"] = " ".join(
            ["%s,%s" % (k, os.path.basename(urlparse.urlsplit(v['uri'])[2]))
             for k, v in json_data['image_data'].items()])
    else:
        raise Exception("Couldn't find any information about images")

    if 'repos' in json_data:
        os.environ["UBUNTU_MIRRORS"] = ",".join([
            "%s|%s|%s|%s" % (
                repo['suite'], repo.get('section', ''), repo['priority'], repo['uri'])
            for repo in json_data['repos']])
    else:
        raise Exception("Couldn't find any information about repos")

    if 'repos' in json_data:
        os.environ["UBUNTU_BASE_MIRROR"] = ",".join([
            "%s|%s|%s|%s" % (
                repo['suite'], repo.get('section', ''), repo['priority'], repo['uri'])
            for repo in json_data['repos'][:1]])
    else:
        raise Exception("Couldn't find any information about repos")
    #FIXME(agordeev): get rid of hardcoded ubuntu release name
    if os.environ['UBUNTU_RELEASE'] == 'trusty':
        os.environ["INSTALL_PACKAGES"] = " ".join(TRUSTY_PACKAGES)
    if 'packages' in json_data:
        os.environ["INSTALL_PACKAGES"] = " ".join(json_data['packages'])


def create_yaml_profile(json_data):
    data = []
    filename = None
    if 'image_data' in json_data:
        for k, v in json_data['image_data'].items():
            filename = os.path.basename(urlparse.urlsplit(v['uri'])[2])
            abs_path = os.path.join(json_data['output'], filename)
            stdout = execute('gunzip', '-ql', abs_path)[0]
            try:
                size = int(stdout.split()[1])
            except (ValueError, KeyError) as e:
                size = None
            stdout = execute('gunzip', '-qc', abs_path, '|', 'md5sum')[0]
            try:
                md5 = stdout.split()[0]
            except (ValueError, KeyError) as e:
                md5 = None
            if not md5 or not size:
                raise Exception("Either md5 or size of %s couldn't be "
                                "calculated" % abs_path)
            data.append({k: {
                'md5': md5,
                'size': size,
                'filename': filename,
                'container': v['container'],
                'format': v['format']}})
        data.append({'repos': json_data['repos']})
    else:
        raise Exception("Couldn't find any information about images")
    filename = os.path.basename(
        urlparse.urlsplit(json_data['image_data']
                                   ['/']['uri'])[2]).split('.')[0]
    with open(os.path.join(json_data['output'], filename + '.yaml'), 'w') as f:
        f.write(yaml.dump(data))


def check_images_do_not_exist(json_data):
    if 'image_data' in json_data:
        for k, v in json_data['image_data'].items():
            filename = os.path.basename(
                urlparse.urlsplit(v['uri'])[2])
            if not os.path.exists(os.path.join(json_data['output'], filename)):
                return True
    return False


def main():
    parser = parse_args()
    params, other_params = parser.parse_known_args()
    try:
        json_data = json.loads(params.json_data)
    except ValueError as exc:
        print "Can't decode json data"
        #FIXME: do logging
        sys.exit(-1)
    else:
        expose_env_params(json_data)
        if check_images_do_not_exist(json_data):
            (stdout, stderr, ret_code) = execute('bash', '-x',
                                                 'create_separate_images.sh')
            if ret_code == 0:
                create_yaml_profile(json_data)
            #FIXME: do logging
            print stdout
            print stderr
            sys.exit(ret_code)


if __name__ == '__main__':
    main()
