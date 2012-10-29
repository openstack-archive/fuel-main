class nailgun::nginx-repo(
  $repo_root = "/var/www/nailgun",
  ){

  file { "/etc/nginx/conf.d/repo.conf":
    content => template("nailgun/nginx_nailgun_repo.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => [
                Package["nginx"],
                ],
    notify => Service["nginx"],
  }

}
