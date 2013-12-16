#!/bin/bash

. $WORKSPACE/utils/jenkins/common.sh

make clean
make $WORKSPACE/build/repos/nailgun.done

cd $WORKSPACE/build/repos/nailgun/docs

# Installing nailgun docs dependencies
sudo pip install -r requirements-docs.txt

make clean
make html
rsync -avz -e ssh --delete _build/html/ fjenkins@fuel-docs.vm.mirantis.net:/home/fjenkins/workspace/fuel-docs.mirantis.com/docs/_build/html/
cd $WORKSPACE
