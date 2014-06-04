# This script automates tagging of release.
# How to use:
# 1. Choose one directory (~/dev/ for example), and fetch all repos there
# 2. Download /etc/nailgun/version.yaml from master node
# 3. cd to fuel-main/utils/ directory
# 4. Run 'python create_tags.py' from this directory

# Author: mihgen

import os
import yaml

with open('version.yaml', "r") as version_file:
    data = yaml.load(version_file.read())

release_number = data['VERSION']['release']

repos = {'fuel-ostf': 'ostf_sha',
         'fuel-main': 'fuelmain_sha',
         'fuel-web': 'nailgun_sha',
         'fuel-astute': 'astute_sha',
         'fuel-library': 'fuellib_sha'}

for repo in repos:
    sha = data['VERSION'][repos[repo]]

    cmd1 = "cd ../../{0}/ && git fetch".format(repo)
    print cmd1
    os.system(cmd1)

    cmd2 = "cd ../../{0}/ && git tag -s {2} {1} -m 'Fuel {2}'".format(
        repo, sha, release_number)
    print cmd2
    os.system(cmd2)

    cmd3 = "cd ../../{0}/ && git push gerrit {1}".format(
        repo, release_number)
    print cmd3
    os.system(cmd3)
