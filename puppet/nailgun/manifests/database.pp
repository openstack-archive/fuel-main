class nailgun::database(
  $user,
  $password,
  $dbname,
  ){
  postgresql::db{ $dbname:
    user     => $user,
    password => $password,
    grant    => 'all',
    require  => Class['::postgresql::server'],
  }
}
