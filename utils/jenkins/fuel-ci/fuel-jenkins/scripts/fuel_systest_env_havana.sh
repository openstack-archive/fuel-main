cd $WORKSPACE

export TEST_NAME=fuelweb_test.integration.test_node:TestNode.test_simple_cluster_flat
export VENV_PATH=/home/jenkins/workspace/venv-nailgun-tests
cp /home/jenkins/workspace/iso/run_tests.py ./fuelweb_test/run_tests.py
cp /home/jenkins/workspace/iso/test_pullrequest.py ./fuelweb_test/tests/test_pullrequest.py

sh -x "/home/jenkins/workspace/system_tests.sh" -t test -i /home/jenkins/workspace/iso/fuel_pull_havana.iso -o --group=setup
