class nailgun::mcollective(
  $mco_pskey = "unset",
  $mco_stompuser = "mcollective",
  $mco_stomppassword = "marionette",
  $rabbitmq_plugins_repo = "file:///var/www/rabbitmq-plugins",
  ){

  class { "mcollective::rabbitmq":
    stompuser => $mco_stompuser,
    stomppassword => $mco_stomppassword,
    rabbitmq_plugins_repo => $rabbitmq_plugins_repo,
  }

  class { "mcollective::client":
    pskey => $mco_pskey,
    stompuser => $mco_stompuser,
    stomppassword => $mco_stomppassword,
    stomphost => $ipaddress,
    stompport => "61613"
  }

}
