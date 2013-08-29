#!/bin/bash

$WORKSPACE/utils/jenkins/common.sh

$WORKSPACE/utils/git-helper/review.py --master-repo $master_repo --master-branch $master_branch --repo $repo --branch $branch --check

# Build checks
[ -z "$pull_title" ] && { echo "ERROR: Specify title for pull request"; exit 1; }
[ -z "$pull_body" ] && { echo "ERROR: Specify body for pull request (how did you test your code??)"; exit 1; }

license_check

# pep8 check for tests. If you need more than this, please create function in review-common.sh
[ -d $WORKSPACE/local_repo/fuelweb_test ] && pep8 fuelweb_test

[ -d $WORKSPACE/local_repo/nailgun ] && nailgun_checks

[ -d $WORKSPACE/local_repo/asute ] && ruby_checks

# Create pull request
$WORKSPACE/utils/git-helper/review.py --repo $repo --branch $branch -t "$pull_title" -b "$pull_body" --add
