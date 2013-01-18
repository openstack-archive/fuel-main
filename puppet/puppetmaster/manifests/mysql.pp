class puppetmaster::mysql(
  $puppet_stored_dbname,
  $puppet_stored_dbuser,
  $puppet_stored_dbpassword,
  $mysql_root_password,
  ) {

  #class { "mysql::server":
  #  config_hash => {
  #    "bind_address" => "127.0.0.1",
  #    "root_password" => $mysql_root_password,
  #  }
  #}

  #mysql::db { $puppet_stored_dbname :
  #  user => $puppet_stored_dbuser,
  #  password => $puppet_stored_dbpassword,
  #}
}
