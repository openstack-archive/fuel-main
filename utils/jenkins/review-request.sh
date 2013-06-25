#!/bin/bash
. $(dirname `readlink -f $0`)/review-common.sh

# Build checks
[ -z "$pull_title" ] && { echo "ERROR: Specify title for pull request"; exit 1; }
[ -z "$pull_body" ] && { echo "ERROR: Specify body for pull request (how did you test your code??)"; exit 1; }

license_check

# pep8 check for tests. If you need more than this, please create function in review-common.sh
pep8 fuelweb_test

nailgun_checks

ruby_checks

# Create pull request
cd $WORKSPACE
./review.py --repo $repo --branch $branch -t "$pull_title" -b "$pull_body" --add
