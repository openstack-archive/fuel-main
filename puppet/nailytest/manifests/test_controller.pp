class nailytest::test_controller {
    file { "/tmp/controller-file":
      content => "Hello world! $role is installed",
    }
    exec { "/bin/sleep 3": }
}
