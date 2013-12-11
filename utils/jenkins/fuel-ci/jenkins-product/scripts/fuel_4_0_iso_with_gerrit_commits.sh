cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH
export ISO_NAME=fuel-gerrit-4.0-$BUILD_NUMBER-$BUILD_ID
export BUILD_DIR=../tmp/$(basename $(pwd))/build
export LOCAL_MIRROR=../tmp/$(basename $(pwd))/local_mirror

# Prepare artifcats dir
mkdir -p artifacts
rm -f artifacts/*

# Patching to add needed functionality
git fetch https://review.openstack.org/stackforge/fuel-main refs/changes/39/58239/3 && git cherry-pick FETCH_HEAD

# Checking gerrit commits for fuel-main
if [ "$fuelmain_gerrit_commit" != "none" ] ; then
  for commit in $fuelmain_gerrit_commit ; do
    git fetch https://review.openstack.org/stackforge/fuel-main $commit && git cherry-pick FETCH_HEAD || false
  done
fi

export NAILGUN_GERRIT_COMMIT="$nailgun_gerrit_commit"
export ASTUTE_GERRIT_COMMIT="$astute_gerrit_commit"
export OSTF_GERRIT_COMMIT="$ostf_gerrit_commit"
export FUELLIB_GERRIT_COMMIT="$fuellib_gerrit_commit"

make deep_clean

make $make_args img

md5sum $BUILD_DIR/iso/$ISO_NAME.iso $BUILD_DIR/iso/$ISO_NAME.img

echo "MD5SUM is:"
md5sum $BUILD_DIR/iso/$ISO_NAME.iso || true
md5sum $BUILD_DIR/iso/$ISO_NAME.img || true

echo "MD5SUM is:"
sha1sum $BUILD_DIR/iso/$ISO_NAME.iso || true
sha1sum $BUILD_DIR/iso/$ISO_NAME.img || true


mv $BUILD_DIR/iso/$ISO_NAME.iso /var/www/fuelweb-iso/
mv $BUILD_DIR/iso/$ISO_NAME.img /var/www/fuelweb-iso/


# dpyzhov comment: let's use less space for our jobs
make deep_clean

echo NAILGUN_GERRIT_COMMIT="$nailgun_gerrit_commit" > artifacts/gerrit_commits.txt
echo ASTUTE_GERRIT_COMMIT="$astute_gerrit_commit" >> artifacts/gerrit_commits.txt
echo OSTF_GERRIT_COMMIT="$ostf_gerrit_commit" >> artifacts/gerrit_commits.txt
echo FUELLIB_GERRIT_COMMIT="$fuellib_gerrit_commit" >> artifacts/gerrit_commits.txt

echo "<a href="http://`hostname -f`/fuelweb-iso/$ISO_NAME.iso">ISO download link</a>"
echo "<a href="http://`hostname -f`/fuelweb-iso/$ISO_NAME.img">IMG download link</a>"
