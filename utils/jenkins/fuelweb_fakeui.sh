#!/bin/bash
topdir=$(dirname `readlink -f $0`)
. $topdir/common.sh

sudo ln -sf $topdir/init.d/nailgun /etc/init.d/nailgun
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun stop

cd $WORKSPACE/nailgun
# Cleaning database
./manage.py dropdb

# Loading data
./manage.py syncdb
./manage.py loaddefault
./manage.py loaddata nailgun/fixtures/sample_environment.json

# Compressing javascript
r.js -o build.js dir=static_compressed

# Starting fake UI
sudo WORKSPACE=$WORKSPACE /etc/init.d/nailgun start
