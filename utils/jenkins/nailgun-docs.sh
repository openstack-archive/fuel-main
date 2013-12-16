#!/bin/bash

. $WORKSPACE/utils/jenkins/common.sh

nailgun_deps

make clean
make $WORKSPACE/build/repos/nailgun.done

cd $WORKSPACE/build/repos/nailgun/docs
make clean
make html
rsync -avz -e ssh --delete _build/html/ jenkins@mos-docs.vm.mirantis.net:/var/www/fuel-dev
cd $WORKSPACE
