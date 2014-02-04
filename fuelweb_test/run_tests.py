def run_tests():
    from proboscis import TestProgram
    from tests import test_admin_node  # NOQA
    from tests import test_ceph  # NOQA
    from tests import test_ha  # NOQA
    from tests import test_neutron  # NOQA
    from tests import test_pullrequest  # NOQA
    from tests import test_services  # NOQA
    from tests import test_simple  # NOQA
    from tests.tests_strength import test_master_node_failover # NOQA

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()
