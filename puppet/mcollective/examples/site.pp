node /fuel-mcollective.mirantis.com/ {

  class { mcollective::rabbitmq:
    user => "mcollective",
    password => "AeN5mi5thahz2Aiveexo",
    vhost => "mcollective",
    stomp => false,
  }

  class { mcollective::client:
    pskey => "un0aez2ei9eiGaequaey4loocohjuch4Ievu3shaeweeg5Uthi",
    user => "mcollective",
    password => "AeN5mi5thahz2Aiveexo",
    host => "127.0.0.1",
    stomp => false,
  }

}
