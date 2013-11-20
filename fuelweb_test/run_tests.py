def run_tests():
    from proboscis import TestProgram
    # from tests import test_admin_node
    # from tests import test_ceph
    # from tests import test_ha
    # from tests import test_neutron
    # from tests import test_services
    from tests import test_simple

    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()
