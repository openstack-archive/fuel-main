#!/bin/bash

. $WORKSPACE/utils/jenkins/common.sh

nailgun_deps

make clean
make $WORKSPACE/build/repos/nailgun.done

cd $WORKSPACE/build/repos/nailgun/docs
make clean
make html
rsync -avz -e ssh --delete _build/html/ fjenkins@fuel-docs.vm.mirantis.net:/home/fjenkins/workspace/fuel-docs.mirantis.com/docs/_build/html/
cd $WORKSPACE
