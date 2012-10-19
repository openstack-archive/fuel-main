class nailytest::test_controller {
    file { "/tmp/controller-file":
      content => "$role",
    }
    exec { "/bin/sleep 3": }
}
