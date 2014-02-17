#!/bin/bash

. $WORKSPACE/utils/jenkins/common.sh

topdir=$WORKSPACE/utils/jenkins

sudo ln -sf $topdir/init.d/nailgun /etc/init.d/nailgun
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun stop

# Installing nailgun dependencies
nailgun_deps

make clean
make $WORKSPACE/build/repos/nailgun.done

cd $WORKSPACE/build/repos/nailgun/nailgun
npm install

# Cleaning database
./manage.py dropdb

# Loading data
./manage.py syncdb
./manage.py loaddefault
./manage.py loaddata nailgun/fixtures/sample_environment.json

# Compressing javascript
grunt build --static-dir=static_compressed

# Replace static path with the one pointing to compressed static content folder
STATIC_DIR=$WORKSPACE/build/repos/nailgun/nailgun/static_compressed
sed 's|_replace_me_static_compressed_path_|'"$STATIC_DIR"'|' -i $topdir/nginx/nailgun.conf
sed 's|_replace_me_static_path_|'"$WORKSPACE"'/build/repos/nailgun/nailgun/static|' -i $topdir/nginx/nailgun.conf
sudo ln -sf $topdir/nginx/nailgun.conf /etc/nginx/conf.d/nailgun.conf
sed 's|^TEMPLATE_DIR:.*$|TEMPLATE_DIR: '"$STATIC_DIR"'|' -i $WORKSPACE/build/repos/nailgun/nailgun/nailgun/settings.yaml
sed 's|^STATIC_DIR:.*$|STATIC_DIR: '"$STATIC_DIR"'|' -i $WORKSPACE/build/repos/nailgun/nailgun/nailgun/settings.yaml
sed 's|^DEVELOPMENT:.*$|DEVELOPMENT: false|' -i $WORKSPACE/build/repos/nailgun/nailgun/nailgun/settings.yaml

# Show date and commit hash in ui, enable mirantis logo
VERSION_TEXT="`git show -s --format=%ci HEAD` `git rev-parse --verify HEAD`"
sed 's|  release:.*$|  release: "'"$VERSION_TEXT"'"|' -i $WORKSPACE/build/repos/nailgun/nailgun/nailgun/settings.yaml
if [ "$MIRANTIS" = "yes" ]; then
  sed 's|  mirantis:.*$|  mirantis: "yes"|' -i $WORKSPACE/build/repos/nailgun/nailgun/nailgun/settings.yaml
fi

# Starting fake UI
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun start
# Reload updated config file
sudo /etc/init.d/nginx reload
