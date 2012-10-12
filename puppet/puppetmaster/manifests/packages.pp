class puppetmaster::packages {

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
  }

  package { "activerecord":
    provider => "gem",
    ensure => "3.0.10",
  }

  package { "mysql":
    provider => "gem", 
    ensure => "2.8.1",
  }
}
