def import_tests():
    from tests import test_admin_node  # noqa
    from tests import test_ceph  # noqa
    from tests import test_environment_action  # noqa
    from tests import test_ha  # noqa
    from tests import test_neutron  # noqa
    from tests import test_pullrequest  # noqa
    from tests import test_services  # noqa
    from tests import test_ha_one_controller  # noqa
    from tests import test_vcenter  # noqa
    from tests.tests_strength import test_failover  # noqa
    from tests.tests_strength import test_master_node_failover  # noqa
    from tests.tests_strength import test_ostf_repeatable_tests  # noqa
    from tests.tests_strength import test_restart  # noqa
    from tests.tests_strength import test_huge_environments  # noqa
    from tests.tests_strength import test_image_based  # noqa
    from tests import test_bonding  # noqa
    from tests.tests_strength import test_neutron  # noqa
    from tests import test_zabbix  # noqa
    from tests import test_upgrade  # noqa
    from tests.plugins.plugin_example import test_fuel_plugin_example  # noqa
    from tests.plugins.plugin_glusterfs import test_plugin_glusterfs  # noqa
    from tests.plugins.plugin_lbaas import test_plugin_lbaas  # noqa
    from tests import test_multiple_networks  # noqa


def run_tests():
    from proboscis import TestProgram  # noqa
    import_tests()

    # Run Proboscis and exit.
    TestProgram().run_and_exit()


if __name__ == '__main__':
    run_tests()
