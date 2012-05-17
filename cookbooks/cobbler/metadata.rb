maintainer        "Mirantis, Inc."
maintainer_email  "product@mirantis.com"
description       "Installs and configures cobbler"
version           "0.0.1"
recipe            "cobbler::default", "Installs cobbler, dnsmasq, tftp-hpa and configures cobbler"

%w{ ubuntu }.each do |os|
  supports os
end

