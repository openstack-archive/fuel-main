# depends: "sample-cook::depend@0.3.0"
# depends: "sample-cook::other_depend@0.3.0"
# depends: "sample-cook::monitor@0.3.0"
File.open('/tmp/chef_success', 'a') {|f| f.puts("default") }
