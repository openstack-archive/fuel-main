class nailytest ($role) {
        case $role[0] {
                "controller" : {
                        include nailytest::test_controller
                }
        }

        case $role[0] {
                "compute" : {
                        include nailytest::test_compute
                }
        }       


}
