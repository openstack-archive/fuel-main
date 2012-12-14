class osnailyfacter::test_controller {
    file { "/tmp/controller-file":
      content => "Hello world! $role is installed",
    }
}
