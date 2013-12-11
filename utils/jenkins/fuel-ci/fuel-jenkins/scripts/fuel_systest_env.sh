cd $WORKSPACE

#sed -i 's/venv-nailgun-tests/workspace\/venv-nailgun-tests/g' "${WORKSPACE}/utils/jenkins/system_tests.sh"
#cp /home/jenkins/workspace/test_admin_node.py "${WORKSPACE}/fuelweb_test/integration/test_admin_node.py"

export TEST_NAME=fuelweb_test.integration.test_node:TestNode.test_simple_cluster_flat
export OPENSTACK_RELEASE="Grizzly on CentOS 6.4"
export VENV_PATH=/home/jenkins/workspace/venv-nailgun-tests
cp /home/jenkins/workspace/iso/run_tests.py ./fuelweb_test/run_tests.py
cp /home/jenkins/workspace/iso/test_pullrequest.py ./fuelweb_test/tests/test_pullrequest.py

#sh -x "/home/jenkins/workspace/system_tests.sh" -K -T integration.test_admin_node:TestAdminNode.test_pull -i #/home/jenkins/workspace/iso/fuel_pull.iso

sh -x "/home/jenkins/workspace/system_tests.sh" -t test -w $WORKSPACE -V $VENV_PATH -V $VENV_PATH -i /home/jenkins/workspace/iso/fuel_pull.iso -o --group=setup
