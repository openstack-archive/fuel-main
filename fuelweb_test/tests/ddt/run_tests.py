def run_tests():
    from proboscis import TestProgram
    import fuelweb_test.tests.ddt.test_deploy

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()