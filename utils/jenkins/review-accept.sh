#!/bin/bash

. $WORKSPACE/utils/jenkins/common.sh

$WORKSPACE/utils/git-helper/review.py --master-repo $master_repo --master-branch $master_branch --repo $repo --branch $branch --check

license_check

# pep8 check for tests. If you need more than this, please create function in review-common.sh
[ -d $WORKSPACE/local_repo/fuelweb_test ] && pep8 fuelweb_test

[ -d $WORKSPACE/local_repo/nailgun ] && nailgun_checks

[ -d $WORKSPACE/local_repo/shotgun ] && shotgun_checks

[ -d $WORKSPACE/local_repo/asute ] && ruby_checks

# Push the branch into master
$WORKSPACE/utils/git-helper/review.py --repo $repo --branch $branch -p
