class one (
  $first = "First parameter",
  $second = "Second parameter"
  ) {
  notify {"sample notification":
    message => "Class parameters: first: $first, second: $second"
  }
  
  file {"sample file":
    path => "/tmp/sample_file",
    source => "modules/one/file_one"
  }

  file {"sample template":
    path => "/tmp/sample_template",
    content => template("one/template_one.erb")
  }
  
  }
