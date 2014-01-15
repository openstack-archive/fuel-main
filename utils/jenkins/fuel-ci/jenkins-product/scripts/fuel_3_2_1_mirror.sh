cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

export BUILD_DIR=../tmp/$(basename $(pwd))/build
export LOCAL_MIRROR=../tmp/$(basename $(pwd))/local_mirror

mirror=3.2.1

export FUELLIB_COMMIT=3.2-fixes
export NAILGUN_COMMIT=3.2-fixes
export ASTUTE_COMMIT=3.2-fixes
export OSTF_COMMIT=3.2-fixes

make deep_clean

for commit in $extra_commits; do
  git fetch https://review.openstack.org/stackforge/fuel-main $commit && git cherry-pick FETCH_HEAD
done

if [ $purge_packages = true ]; then
  extra="$extra --del"
fi

make USE_MIRROR=none mirror

sudo rsync $LOCAL_MIRROR/* /var/www/fwm/$mirror/ -r -t -v $extra
sudo createrepo -g /var/www/fwm/$mirror/centos/os/x86_64/repodata/comps.xml -o /var/www/fwm/$mirror/centos/os/x86_64 /var/www/fwm/$mirror/centos/os/x86_64

mirrors_fail=""
ssh jenkins@srv08-srt.srt.mirantis.net sudo chown -R jenkins /var/www/fwm/$mirror/ || true
rsync /var/www/fwm/$mirror/* srv08-srt.srt.mirantis.net:/var/www/fwm/$mirror/ -r -t -v $extra || mirrors_fail+=" srv08"

rsync /var/www/fwm/$mirror/* rsync://backup.kha.mirantis.net/ostf-mirror/fwm/$mirror/ -r -t -v $extra || mirrors_fail+=" kha"

rsync /var/www/fwm/$mirror/* ss0078.svwh.net:/var/www/fwm/$mirror/ -r -t -v $extra || mirrors_fail+=" us"

ssh srv08-srt.srt.mirantis.net sudo rsync -vaP /var/www/fwm/$mirror/ rsync://repo.srt.mirantis.net/repo/fuelweb-repo/$mirror/ -c $extra || mirrors_fail+=" ext"

if [[ -n "$mirrors_fail" ]]; then
  echo Some mirrors failed to update: $mirrors_fail
  exit 1
fi
