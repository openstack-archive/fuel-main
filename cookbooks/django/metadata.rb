maintainer        "Mirantis Inc."
maintainer_email  "product@mirantis.com"
license           "Apache 2.0"
description       "Installs Django"
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.rdoc'))
version           "0.0.1"

recipe "django", "Installs django and apache2 with mod_python"

%w{ubuntu}.each do |os|
  supports os
end

%w{apache2 python}.each do |cb|
  depends cb
end
