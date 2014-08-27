# == Class: mongodb::db
#
# Class for creating mongodb databases and users.
#
# == Parameters
#
#  user - Database username.
#  password_hash - Hashed password. Hex encoded md5 hash of "$username:mongo:$password".
#  password - Plain text user password. This is UNSAFE, use 'password_hash' unstead.
#  roles (default: ['dbAdmin']) - array with user roles.
#  tries (default: 10) - The maximum amount of two second tries to wait MongoDB startup.
#
define mongodb::db (
  $user,
  $password_hash = false,
  $password      = false,
  $roles         = ['dbAdmin'],
  $tries         = 10,
  $admin_username = undef,
  $admin_password = undef,
  $admin_host     = undef,
  $admin_database = undef,
) {

  mongodb_database { $name:
    ensure   => present,
    tries    => $tries,
    admin_username  => $admin_username,
    admin_password  => $admin_password,
    admin_host      => $admin_host,
    admin_database  => $admin_database,
    require         => Class['mongodb::server'],
  }

  if $password_hash {
    $hash = $password_hash
  } elsif $password {
    $hash = mongodb_password($user, $password)
  } else {
    fail("Parameter 'password_hash' or 'password' should be provided to mongodb::db.")
  }

  mongodb_user { $user:
    ensure        => present,
    password_hash => $hash,
    database      => $name,
    roles         => $roles,
    admin_username  => $admin_username,
    admin_password  => $admin_password,
    admin_host      => $admin_host,
    admin_database  => $admin_database,
    require       => Mongodb_database[$name],
  }

}
