class puppetmaster::packages(
  $puppet_package_version = "2.7.19-1.el6",
  $gem_source="http://rubygems.org/",
  ){

  define puppetmaster_safe_package($version = ""){
    if $version != "" {
      $ensure = $version
    }
    else {
      $ensure = "present"
    }

    if ! defined(Package[$name]){
      @package { $name :
        ensure => $ensure
      }
    }
  }

  puppetmaster_safe_package{ "ruby-devel": }
  puppetmaster_safe_package{ "rubygems": }
  puppetmaster_safe_package{ "make": }
  puppetmaster_safe_package{ "gcc": }
  puppetmaster_safe_package{ "gcc-c++": }

  puppetmaster_safe_package{ "puppet-server":
    version => $puppet_package_version,
  }
  puppetmaster_safe_package{ "rubygem-mongrel": }
  puppetmaster_safe_package{ "nginx": }
  puppetmaster_safe_package{ "puppetdb-terminus": }


  Puppetmaster_safe_package<| title == "ruby-devel" |> ->
  Puppetmaster_safe_package<| title == "rubygems" |> ->
  Puppetmaster_safe_package<| title == "make" |> ->
  Puppetmaster_safe_package<| title == "gcc" |> ->
  Puppetmaster_safe_package<| title == "gcc-c++" |> ->

  Package<| provider == "gem" |> ->

  Puppetmaster_safe_package<| title == "rubygem-mongrel" |> ->
  Puppetmaster_safe_package<| title == "puppet-server" |>

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
}
