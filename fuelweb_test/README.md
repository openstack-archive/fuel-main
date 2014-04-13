For Ubuntu 12.10 server
=======================
To run tests
------------

[Devops documentation](http://docs.mirantis.com/fuel-dev/devops.html)

For 'make iso'
--------------

[Building ISO documentation](http://docs.mirantis.com/fuel-dev/develop/env.html#building-the-fuel-iso)

Important notes for Savanna and Murano tests
--------------------------------------------
 * Don't recommend to start tests without kvm
 * Put Savanna image savanna-0.3-vanilla-1.2.1-ubuntu-13.04.qcow2 (md5 9ab37ec9a13bb005639331c4275a308d)
to /tmp/ before start for best performance. If Internet available the image will download automatically.
 * Put Murano image cloud-fedora.qcow2 (md5 6e5e2f149c54b898b3c272f11ae31125) to /tmp/ before start.
Murano image available only internally.
 * Murano tests  without Internet connection on the instances will be failed
 * For Murano tests execute 'export SLAVE_NODE_MEMORY=5120' before tests run.
 * To get heat autoscale tests passed put image F17-x86_64-cfntools.qcow2 in /tmp before start

Run single OSTF tests several times
-----------------------------------
 * Export environment variable OSTF_TEST_NAME. Example: export OSTF_TEST_NAME='Request list of networks'
 * Export environment variable OSTF_TEST_RETRIES_COUNT. Example: export OSTF_TEST_RETRIES_COUNT=120
 * Execute test_ostf_repetable_tests from tests_strength package

       sh "utils/jenkins/system_tests.sh" -t test -w $(pwd) -j "fuelweb_test" -i "$ISO_PATH" -V $(pwd)/venv/fuelweb_test -o --group=create_delete_ip_n_times_nova_flat
