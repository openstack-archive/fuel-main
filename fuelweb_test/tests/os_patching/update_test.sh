#!/bin/sh

ENV_ID="${1}"
VERSION="${2}"
OS="${3}"
MASTER_IP="${4}"

if [ "${1}" = "help" ]; then
  echo "${0} (env_id) (version) (os) (master_ip)"
  echo "default: ${0} 1 5.1 centos 10.20.0.2" 
  exit 0
fi

if [ "${ENV_ID}" == "" ]; then
  ENV_ID="1"
fi

if [ "${VERSION}" == "" ]; then
  VERSION="5.1"
fi

if [ "${OS}" == "" ]; then
  OS="centos"
fi

if [ "${MASTER_IP}" == "" ]; then
  MASTER_IP="10.20.0.2"
fi

### functions ###

# basic #

upload_from_stdin() {
  dockerctl shell "${1}" "tee ${2}" > /dev/null
}

set_all_error() {
cat <<EOF | upload_from_stdin nailgun set_all_error.sh
  python -c "
status = 'error'
from nailgun.db import db
from nailgun.db.sqlalchemy.models import Node
from nailgun.objects import Cluster

cluster = Cluster.get_by_uid(${ENV_ID})
if not cluster:
    print 'No cluster: ' + '${ENV_ID}'
    exit(1)
Cluster.update(cluster, {'status': status})
print \"Set cluster '%d' to '%s'\" % (${ENV_ID}, status) 
db().commit()

nodes = db().query(Node).filter_by(cluster_id=${ENV_ID})

for node in nodes:
  node_db = db().query(Node).get(node.id)
  setattr(node_db, 'status', 'error')
  print \"Set node '%d' to '%s'\" % (node.id, status)
  db().add(node_db)
  db().commit()
"
  if [ \$? -gt 0 ]; then
    echo "Could not set node status to error!"
    exit 1
  fi
EOF
  dockerctl shell nailgun "sh set_all_error.sh"
}

fuel_deploy_changes() {
  fuel --env "${ENV_ID}" deploy-changes
  if [ $? -gt 0 ]; then
    echo "Deploy run have failed!"
    exit 1
  fi
}

fuel_download_deployment_config() {
  fuel --env "${ENV_ID}" deployment default
  if [ $? -gt 0 ]; then
    fuel --env "${ENV_ID}" deployment download
    if [ $? -gt 0 ]; then
      echo "Could not download node's config!"
      exit 1
    fi
  fi

  YAML_DIR="deployment_${ENV_ID}"
}

fuel_upload_deployment_config() {
  fuel --env "${ENV_ID}" deployment upload
  if [ $? -gt 0 ]; then
    echo "Could not upload node's config!"
    exit 1
  fi
  rm -rf "${YAML_DIR}"
}

# advanced #

set_yaml_data() {
  version="${1}"
  fuel_download_deployment_config
  for file in ${YAML_DIR}/*.yaml; do
    echo "Processing ${file}"
    ruby -e "
  require 'yaml'
  file='${file}'
  yaml = YAML.load_file file
  unless yaml
    puts 'Could not load env settings form ' + file
    exit 1
  end
  version_data_centos = {
    '5.0' => {
      'repo_metadata' => {
        'nailgun' => 'http://${MASTER_IP}:8080/centos/fuelweb/x86_64/',
      },
      'puppet_modules_source'   => 'rsync://${MASTER_IP}/puppet/releases/5.0/modules/',
      'puppet_manifests_source' => 'rsync://${MASTER_IP}/puppet/releases/5.0/manifests/',
    },
    '5.1' => {
      'repo_metadata' => {
        'nailgun' => 'http://${MASTER_IP}:8080/centos/fuelweb/x86_64/',
        'update'  => 'http://${MASTER_IP}:8080/centos-fuel-5.1-update/centos/',
      },
      'puppet_modules_source'   => 'rsync://${MASTER_IP}/puppet/releases/5.1/modules/',
      'puppet_manifests_source' => 'rsync://${MASTER_IP}/puppet/releases/5.1/manifests/',
    },
  }
  version_data_ubuntu = {
    '5.0' => {
      'repo_metadata' => {
        'nailgun' => 'http://${MASTER_IP}:8080/ubuntu/fuelweb/x86_64 precise main',
      },
      'puppet_modules_source'   => 'rsync://${MASTER_IP}/puppet/releases/5.0/modules/',
      'puppet_manifests_source' => 'rsync://${MASTER_IP}/puppet/releases/5.0/manifests/',
    },
    '5.1' => {
      'repo_metadata' => {
        'nailgun' => 'http://${MASTER_IP}:8080/ubuntu/fuelweb/x86_64 precise main',
        'update'  => 'http://${MASTER_IP}:8080/ubuntu-fuel-5.1-update/reprepro/ precise main',
      },
      'puppet_modules_source'   => 'rsync://${MASTER_IP}/puppet/releases/5.1/modules/',
      'puppet_manifests_source' => 'rsync://${MASTER_IP}/puppet/releases/5.1/manifests/',
    },
  }

  version_data = version_data_${OS}

  unless version_data.key? '${version}'
    puts 'No such version in data structure ${version}'
    exit 1
  end
  yaml = yaml.merge version_data['${version}']
  File.open(file, 'w') { |file| file.write YAML.dump yaml }
  puts 'File ' + file + ' was updated'
"
    if [ $? -gt 0 ]; then
      echo "Could not set yaml data to version ${version}"
      exit 1
    fi
  done
  fuel_upload_deployment_config
}

update() {
  set_all_error
  set_yaml_data "${1}"
  add_repo_keys
  fuel_deploy_changes
  get_pkg_version
}

get_node_ip() {
  id="${1}"
  fuel nodes | ruby -n -e "
    line = \$_.split('|').map { |f| f.chomp.strip }
    puts line[4] if line[0] == '${id}' and line[3] == '${ENV_ID}'
  "
}

get_env_node_ids() {
  fuel nodes | ruby -n -e "
    line = \$_.split('|').map { |f| f.chomp.strip }
    puts line[0] if line[3] == '${ENV_ID}'
  "
}

add_repo_keys() {
  if [ "${OS}" != "ubuntu" ]; then
    return
  fi
  id="${1}"

  ids=$(get_env_node_ids)
  for id in ${ids}; do
    ip=$(get_node_ip "${id}")
    cat "mirantis.key" | ssh "${ip}" "apt-key add -"
  done
}

get_pkg_version() {
  ids=$(get_env_node_ids)
  for id in ${ids}; do
    ip=$(get_node_ip ${id})
    if [ "${ip}" = "" ]; then
      continue
    fi

    if [ "${OS}" = "centos" ]; then
      ssh "${ip}" "rpm -qa openstack-glance"
    elif [ "${OS}" = "ubuntu" ]; then
      ssh "${ip}" "dpkg -l glance-api"  | grep "^ii"
    else
      break
    fi
  done
}

### MAIN ###

update "${VERSION}"
