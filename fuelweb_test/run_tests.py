def run_tests():
    from proboscis import TestProgram

    from tests import test_admin_node  # noqa
    from tests import test_ceph  # noqa
    from tests import test_environment_action  # noqa
    from tests import test_ha  # noqa
    from tests import test_neutron  # noqa
    from tests import test_pullrequest  # noqa
    from tests import test_services  # noqa
    from tests import test_simple  # noqa
    from tests.tests_strength import test_failover  # noqa
    from tests.tests_strength import test_master_node_failover  # noqa
    from tests.tests_strength import test_ostf_repeatable_tests  # noqa
    from tests.tests_strength import test_restart  # noqa
    from tests.tests_strength import test_huge_environments  # noqa
    from tests import test_bonding  # noqa

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()
