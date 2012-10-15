class nailytest {
        case $role {
                "test_controller" : {
                        include nailytest::test_controller
                }
        }

        case $role {
                "test_compute" : {
                        include nailytest::test_compute
                }
        }       
}
