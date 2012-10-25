class puppetmaster::packages(
  $gem_source="http://rubygems.org/",
  ){

  # define puppetmaster_safe_package(){
  #   if ! defined(Package[$name]){
  #     @package { $name : }
  #   }
  # }
  
  # puppetmaster_safe_package{ "mysql-devel": }
  # puppetmaster_safe_package{ "ruby-devel": }
  # puppetmaster_safe_package{ "rubygems": }
  # puppetmaster_safe_package{ "make": }
  # puppetmaster_safe_package{ "gcc": }

  package { "mysql-devel": } ->
  package { "ruby-devel": } ->
  package { "rubygems": } ->
  package { "make": } ->
  package { "gcc": } ->
  Package<| provider == "gem" |>

  # http://projects.puppetlabs.com/issues/9290
  package { "rails":
    provider => "gem",
    ensure => "3.0.10",
    source => $gem_source,
  }

  package { "activerecord":
    provider => "gem",
    ensure => "3.0.10",
    source => $gem_source,
  }

  package { "mysql":
    provider => "gem", 
    ensure => "2.8.1",
    source => $gem_source,
  }
}
