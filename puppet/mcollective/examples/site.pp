node /fuel-mcollective.mirantis.com/ {

  class { mcollective::rabbitmq:
    stompuser => "mcollective",
    stomppassword => "AeN5mi5thahz2Aiveexo",
  }

  class { mcollective::client:
    pskey => "un0aez2ei9eiGaequaey4loocohjuch4Ievu3shaeweeg5Uthi",
    stompuser => "mcollective",
    stomppassword => "AeN5mi5thahz2Aiveexo",
    stomphost => "127.0.0.1",
    stompport => "61613"
  }

}
