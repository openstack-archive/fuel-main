class nailytest::test_compute {
    file { "/tmp/compute-file":
      content => "$meta",
    }
}
