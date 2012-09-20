maintainer        "Benjamin Black"
maintainer_email  "b@b3k.us"
license           "Apache 2.0"
description       "Installs and configures RabbitMQ server"
version           "0.1"
recipe            "rabbitmq::cluster", "Set up RabbitMQ clustering."
recipe            "rabbitmq", "Set up simple RabbitMQ daemon."

%w{centos redhat ubuntu debian}.each do |os|
  supports os
end
