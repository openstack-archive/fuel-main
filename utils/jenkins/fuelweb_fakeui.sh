#!/bin/bash

$WORKSPACE/utils/jenkins/common.sh

topdir=$WORKSPACE/utils/jenkins

sudo ln -sf $topdir/init.d/nailgun /etc/init.d/nailgun
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun stop

# Installing nailgun dependencies
nailgun_deps

make clean
make $WORKSPACE/build/repos/nailgun.done

cd $WORKSPACE/build/repos/nailgun/nailgun
# Cleaning database
./manage.py dropdb

# Loading data
./manage.py syncdb
./manage.py loaddefault
./manage.py loaddata nailgun/fixtures/sample_environment.json

# Compressing javascript
r.js -o build.js dir=static_compressed

# Replace static path with the one pointing to compressed static content folder
sed 's|_replace_me_static_compressed_path_|'"$WORKSPACE"'/nailgun/static_compressed|' -i $topdir/nginx/nailgun.conf
sed 's|_replace_me_static_path_|'"$WORKSPACE"'/nailgun/static|' -i $topdir/nginx/nailgun.conf
sudo ln -sf $topdir/nginx/nailgun.conf /etc/nginx/conf.d/nailgun.conf

# Starting fake UI
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun start
# Reload updated config file
sudo /etc/init.d/nginx reload
