class nailytest::test_rpuppet ($rpuppet) {
    file { "/tmp/test_rpuppet":
      content => "Hello from RPuppet! rpuppet = $rpuppet is set!\n hashes=$hashes\n",
    }
}
