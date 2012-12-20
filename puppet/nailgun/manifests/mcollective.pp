class nailgun::mcollective(
  $mco_pskey = "unset",
  $mco_stompuser = "mcollective",
  $mco_stomppassword = "marionette",
  ){

  class { "mcollective::rabbitmq":
    stompuser => $mco_stompuser,
    stomppassword => $mco_stomppassword,
  }

  class { "mcollective::client":
    pskey => $mco_pskey,
    stompuser => $mco_stompuser,
    stomppassword => $mco_stomppassword,
    stomphost => $ipaddress,
    stompport => "61613"
  }

}
