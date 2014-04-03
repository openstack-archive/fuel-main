#!/bin/bash -e
BUILD_DIR="$PWD/../build"
mkdir -p $BUILD_DIR/docker $BUILD_DIR/isoroot

fuellibrepo="https://github.com/stackforge/fuel-library.git"

#TODO refactor to check ENV for this value
fuellibref="origin/master"
FUELLIB_GERRIT_URL="https://review.openstack.org/stackforge/fuel-library"
declare -A containers
if [ -z "$1" ] ; then
  for candidate in *; do
    [ -d "$candidate" ] && containers+="$candidate "
  done
else
  containers=$@
fi

mkdir -p $BUILD_DIR/docker
for container in $containers; do
  . $container/config
  #config has these vars
  #dockerrepo=git://repo.git
  #dockerref=master
  #puppetrepo=git://repo.git
  #puppetref=refs/changes/61/83061/4

  rm -rf "$BUILD_DIR/docker/$container"
  git clone --depth 1 --branch $dockerref $dockerrepo $BUILD_DIR/docker/$container
  if [ "$puppetref" != "none" -a "$puppetref" != "same" ]; then
    rm -rf $BUILD_DIR/docker/puppet
    if grep -q "refs/changes" <<< "$puppetref"; then
      git clone --depth 50 --branch master $puppetrepo $BUILD_DIR/docker/puppet
      pushd $BUILD_DIR/docker/puppet
      for gerrit_change in "${puppetref[@]}"; do
        git fetch "$FUELLIB_GERRIT_URL" "$gerrit_change"
        git cherry-pick FETCH_HEAD
      done
      popd
    else
      git clone --depth 1 --branch $puppetref $puppetrepo $BUILD_DIR/docker/puppet
    fi
    rm -rf "$BUILD_DIR/docker/$container/etc/puppet/modules"
    mkdir -p "$BUILD_DIR/docker/$container/etc/puppet/modules"
    cp -R $BUILD_DIR/docker/puppet/deployment/puppet/* $BUILD_DIR/docker/$container/etc/puppet/modules
  elif [ "$puppetref" = "same" ];then
    mkdir -p "$BUILD_DIR/docker/$container/etc/puppet/modules"
    pushd "$BUILD_DIR/docker/$container/etc/puppet/modules"
    git init puppet
    git remote add puppet $fuellibrepo
    git fetch puppet $fuellibref
    git checkout FETCH_HEAD
    popd
  fi
  pushd $BUILD_DIR/docker/
  docker build -t fuel/$container $container
  #Run once to create an exportable container
  #container_id=$(docker run -d fuel/$container echo export only)
  mkdir -p "${BUILD_DIR}/isoroot/docker/"
  #docker export $container_id | xz -zc > "${BUILD_DIR}/isoroot/docker/${container}.tar.xz"
  docker save fuel/$container | xz -zc -T0 > "${BUILD_DIR}/isoroot/docker/${container}.tar.xz"
  popd
done
