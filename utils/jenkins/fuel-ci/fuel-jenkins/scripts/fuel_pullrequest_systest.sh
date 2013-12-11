cd $WORKSPACE

#common params
export LOGS_DIR=/home/jenkins/workspace/fuel_pullrequest_systest/logs
export TEST_NAME=fuelweb_test.integration.test_node:TestNode.test_simple_cluster_flat
export UPLOAD_MANIFESTS=true
export UPLOAD_MANIFESTS_PATH=/home/jenkins/workspace/fuel_pullrequest_systest/deployment/puppet/
export VENV_PATH=/home/jenkins/workspace/venv-nailgun-tests

is_havana=`echo "${ghprbTargetBranch}" | grep -i master | wc -l`

if [ $is_havana -gt 0 ]; then
 export WORKSPACE=/home/jenkins/workspace/fuel_systest_env_havana
 export ENV_NAME="fuel_systest_env_havana_system_test"
 export ISO_PATH="/home/jenkins/workspace/iso/fuel_pull_havana.iso"
else
 export WORKSPACE=/home/jenkins/workspace/fuel_systest_env
 export ENV_NAME="fuel_systest_env_system_test"
 export OPENSTACK_RELEASE="Grizzly on CentOS 6.4"
 export ISO_PATH="/home/jenkins/workspace/iso/fuel_pull.iso"
fi

sh -x "/home/jenkins/workspace/system_tests.sh" -k -t test -i "${ISO_PATH}" -o --group=test_pullrequest
