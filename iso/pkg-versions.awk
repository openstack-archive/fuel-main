#!/usr/bin/awk -f

# Parse repos databases and generate versions.yaml files for patching
# Usage:
#   rpm -qi -p /path/to/repo/Packages/*.rpm | versions.awk > centos-versions.yaml
#   cat /path/to/repo/dists/precise/main/binary-amd64/Packages | versions.awk > ubuntu-version.yaml
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

  deb_blacklist["ceph"] = 1
  deb_blacklist["ceph-common"] = 1
  deb_blacklist["ceph-common-dbg"] = 1
  deb_blacklist["ceph-dbg"] = 1
  deb_blacklist["ceph-deploy"] = 1
  deb_blacklist["ceph-fs-common"] = 1
  deb_blacklist["ceph-fs-common-dbg"] = 1
  deb_blacklist["ceph-fuse"] = 1
  deb_blacklist["ceph-fuse-dbg"] = 1
  deb_blacklist["ceph-mds"] = 1
  deb_blacklist["ceph-mds-dbg"] = 1
  deb_blacklist["ceph-resource-agents"] = 1
  deb_blacklist["ceph-test"] = 1
  deb_blacklist["ceph-test-dbg"] = 1
  deb_blacklist["libcephfs-dev"] = 1
  deb_blacklist["libcephfs-java"] = 1
  deb_blacklist["libcephfs-jni"] = 1
  deb_blacklist["libcephfs1"] = 1
  deb_blacklist["libcephfs1-dbg"] = 1
  deb_blacklist["librados-dev"] = 1
  deb_blacklist["librados2"] = 1
  deb_blacklist["librados2-dbg"] = 1
  deb_blacklist["librbd-dev"] = 1
  deb_blacklist["librbd1"] = 1
  deb_blacklist["librbd1-dbg"] = 1
  deb_blacklist["python-ceph"] = 1
  deb_blacklist["radosgw"] = 1
  deb_blacklist["radosgw-dbg"] = 1
  deb_blacklist["rbd-fuse"] = 1
  deb_blacklist["rbd-fuse-dbg"] = 1
  deb_blacklist["rest-bench"] = 1
  deb_blacklist["rest-bench-dbg"] = 1
}
/^Name /{ name=$3}
/^Version /{ version=$3}
/^Release /{
  if (name in rpm_blacklist == 0) {
    print name ": \"" version "-" $3 "\""
  }
}
/^Package:/{ name=$2 }
/^Version:/{
  if (name in deb_blacklist == 0) {
    print name ": \"" $2 "\""
  }
}
