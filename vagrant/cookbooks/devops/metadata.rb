maintainer       "Mirantis, Inc."
maintainer_email "product@mirantis.com"
license          "BSD"
description      "Installs/Configures devops"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          "0.0.1"
recipe           "deps", "Install devops prerequisites"

supports "ubuntu"

%w{python}.each do |cookbook|
  depends cookbook
end


