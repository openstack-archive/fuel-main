#!/usr/bin/awk -f

# Parse repos databases and generate versions.yaml files for patching
# Usage:
#   rpm -qi -p /path/to/repo/Packages/*.rpm | versions.awk > centos-versions.yaml
#   cat /path/to/repo/dists/precise/main/binary-amd64/Packages | versions.awk > ubuntu-version.yaml
/^Name /{ name=$3}
/^Version /{ version=$3}
/^Release /{ print name ": \"" version "-" $3 "\""}
/^Package:/{ name=$2 }
/^Version:/{ print name ": \"" $2 "\""}
