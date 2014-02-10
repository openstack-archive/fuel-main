def run_tests():
    from proboscis import TestProgram
    from tests import test_admin_node
    from tests import test_ceph
    from tests import test_ha
    from tests import test_neutron
    from tests import test_services
    from tests import test_simple
    from tests import test_pullrequest
    from tests.tests_strength import test_master_node_failover
    from tests.tests_strength import test_failover
    from tests.tests_strength import test_huge_environments  # noqa
    from tests.tests_strength import test_restart

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()
