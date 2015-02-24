#!/usr/bin/awk -f

# Parse repos databases and generate versions.yaml files for patching
# Usage:
#   rpm -qi -p /path/to/repo/Packages/*.rpm | versions.awk > centos-versions.yaml
BEGIN{
  rpm_blacklist["ceph"] = 1
  rpm_blacklist["ceph-debuginfo"] = 1
  rpm_blacklist["ceph-deploy"] = 1
  rpm_blacklist["ceph-devel"] = 1
  rpm_blacklist["ceph-fuse"] = 1
  rpm_blacklist["ceph-radosgw"] = 1
  rpm_blacklist["ceph-test"] = 1
  rpm_blacklist["cephfs-java"] = 1
  rpm_blacklist["libcephfs1"] = 1
  rpm_blacklist["libcephfs_jni1"] = 1
  rpm_blacklist["librados2"] = 1
  rpm_blacklist["librbd1"] = 1
  rpm_blacklist["python-ceph"] = 1
  rpm_blacklist["rbd-fuse"] = 1
  rpm_blacklist["rest-bench"] = 1
}
/^Name /{ name=$3}
/^Version /{ version=$3}
/^Release /{
  if (name in rpm_blacklist == 0) {
    print name ": \"" version "-" $3 "\""
  }
}