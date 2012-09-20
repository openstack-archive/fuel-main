maintainer       "Mirantis Inc."
maintainer_email "product@mirantis.com"
license          "Apache 2.0"
description      "Installs/Configures nailgun"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          "0.0.1"
recipe           "server", "Include Nailgun daemon install/configuration"
recipe           "network", "Setup network configuration based on node's 'networks' attribute"
recipe           "deps", "Installs nailgun deps"

supports "ubuntu" # It should work on debian too, but not tested yet

%w{python cobbler}.each do |cookbook|
  depends cookbook
end

attribute "nailgun/root",
  :display_name => "Root directory",
  :description  => "Nailgun daemon root directory",
  :default      => "/opt/nailgun"

attribute "nailgun/user",
  :display_name => "Nailgun user",
  :description  => "Nailgun daemon user",
  :default      => "nailgun"

attribute "networks",
  :display_name => "Networks' definition",
  :description  => "Node networks' definition"

