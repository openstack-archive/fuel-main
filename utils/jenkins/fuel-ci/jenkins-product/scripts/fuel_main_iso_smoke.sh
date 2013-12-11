cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

rm -rf logs/*

export TEST_NAME=fuelweb_test.integration.test_node:TestNode.test_simple_cluster_flat
ISO_BUILD=`echo $ISO_PATH | cut -d- -f4`

VENV_PATH=/home/jenkins/venv-nailgun-tests

if echo $ISO_PATH | grep -qi "fuel-3.2.1" ; then
  export OPENSTACK_RELEASE="Grizzly on CentOS 6.4"
  ISO_RELEASE="fuel_3_2_1_iso"
else
  ISO_RELEASE="fuel_4_0_iso"
fi

export ISO_URL=`wget 2>/dev/null -O - "http://jenkins-product.srt.mirantis.net:8080/job/${ISO_RELEASE}/${ISO_BUILD}/api/xml/?xpath=/freeStyleBuild/description" | grep href | sed -e 's/<description>\&lt;a href=//g; s/\&gt.*//g'`

sh -x "utils/jenkins/system_tests.sh" -t test -w $WORKSPACE -V $VENV_PATH -j $JOB_NAME -U "${ISO_URL}" -o --group=deploy_simple_flat
