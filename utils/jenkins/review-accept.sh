#!/bin/bash
. $(dirname `readlink -f $0`)/review-common.sh

license_check

# pep8 check for tests. If you need more than this, please create function in review-common.sh
pep8 fuelweb_test

nailgun_checks

ruby_checks

# Push the branch into master
$WORKSPACE/review.py --repo $repo --branch $branch -p
