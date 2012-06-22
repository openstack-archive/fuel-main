maintainer        "Mirantis, Inc."
maintainer_email  "product@mirantis.com"
description       "Installs and configures cobbler"
version           "0.0.1"
recipe            "cobbler::default", "Installs cobbler, dnsmasq, tftp-hpa and configures cobbler"
recipe            "cobbler::bootstrap", "Installs bootstrap distro, profile and system"
recipe            "cobbler::precise-x86_64", "Installs precise-x86_64 distro and profile"

%w{ ubuntu }.each do |os|
  supports os
end

