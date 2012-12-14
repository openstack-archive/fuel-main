class osnailyfacter::test_compute {
    file { "/tmp/compute-file":
      content => "Hello world! $role is installed",
    }
}
