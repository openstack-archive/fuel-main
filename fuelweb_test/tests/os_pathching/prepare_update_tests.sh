#!/bin/sh
centos_repo_archive="centos-fuel-5.1-update.tgz"
ubuntu_repo_archive="ubuntu-fuel-5.1-update.tgz"
repos_dir="/var/www/nailgun"

puppet_releases="/etc/puppet/releases"
puppet_modules="/etc/puppet/modules"
puppet_manifests="/etc/puppet/manifests"

modules_versions='5.0 5.1'

### functions ###

upload_from_stdin() {
  dockerctl shell "${1}" "tee ${2}" > /dev/null
}

prepare_versioned_puppet() {
cat <<EOF | upload_from_stdin rsync puppet_modules_update.sh

  modules_versions='${modules_versions}'

  if ! [ -d "${puppet_modules}" ]; then
    exit 1
  fi

  if ! [ -d "${puppet_manifests}" ]; then
    exit 1
  fi
  
  for version in ${modules_versions}; do
    mkdir -p "${puppet_releases}/\${version}/modules"
    mkdir -p "${puppet_releases}/\${version}/manifests"
    rsync -ca --delete "${puppet_modules}/" "${puppet_releases}/\${version}/modules/"
    rsync -ca --delete "${puppet_manifests}/" "${puppet_releases}/\${version}/manifests/"
  done

EOF

  dockerctl shell rsync "sh puppet_modules_update.sh"

}

create_versions_files() {
cat <<EOF | upload_from_stdin rsync "${puppet_releases}/5.0/manifests/centos-versions.yaml"
---
openstack-glance: "2014.1.fuel5.0-mira3"
EOF

cat <<EOF | upload_from_stdin rsync "${puppet_releases}/5.1/manifests/centos-versions.yaml"
---
openstack-glance: "2014.1.fuel5.0-mira999"
EOF

cat <<EOF | upload_from_stdin rsync "${puppet_releases}/5.0/manifests/ubuntu-versions.yaml"
---
glance-api: 1:2014.1.fuel5.0~mira5
EOF

cat <<EOF | upload_from_stdin rsync "${puppet_releases}/5.1/manifests/ubuntu-versions.yaml"
---
glance-api: 1:2014.1.fuel5.0~mira999
EOF
}

untar_repos() {
  cat "${centos_repo_archive}" | upload_from_stdin nginx "${centos_repo_archive}"
  cat "${ubuntu_repo_archive}" | upload_from_stdin nginx "${ubuntu_repo_archive}"
  dockerctl shell nginx "yum install -y -q tar"
  dockerctl shell nginx "tar -C ${repos_dir} -xf ${centos_repo_archive}"
  dockerctl shell nginx "tar -C ${repos_dir} -xf ${ubuntu_repo_archive}"
}

cd_home() {
  DIR=$(dirname "${0}")
  cd "${DIR}"
  if [ $? -gt 0 ]; then
    echo "Could not cd to ${DIR}!"
    exit 1
  fi
}

## MAIN ##

cd_home
prepare_versioned_puppet
create_versions_files
untar_repos
