#!/bin/bash

$WORKSPACE/utils/jenkins/common.sh

$WORKSPACE/utils/git-helper/review.py --master-repo $master_repo --master-branch $master_branch --repo $repo --branch $branch --check

nailgun_deps

cd $WORKSPACE/local_repo/docs
make clean
make html
rsync -avz -e ssh --delete _build/html/ fjenkins@fuel-docs.vm.mirantis.net:/home/fjenkins/workspace/fuel-docs.mirantis.com/docs/_build/html/
cd $WORKSPACE
