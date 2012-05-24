maintainer        "Mirantis, Inc."
maintainer_email  "product@mirantis.com"
description       "Installs and configures cobbler"
version           "0.0.1"
recipe            "aptrepo::frompool", "Creates repo from directory with deb packages"

%w{ ubuntu }.each do |os|
  supports os
end

