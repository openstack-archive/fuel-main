maintainer       "Maxim Kulkin"
maintainer_email "mkulkin@mirantis.com"
license          "BSD"
description      "Installs/Configures nailgun"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          "0.0.1"
recipe           "server", "Include Nailgun daemon install/configuration"

supports "ubuntu" # It should work on debian too, but not tested yet

%w{celery redis django python}.each do |cookbook|
  depends cookbook
end

attribute "nailgun/root",
  :display_name => "Root directory",
  :description  => "Nailgun daemon root directory",
  :default      => "/vagrant/ngui"

attribute "nailgun/user",
  :display_name => "Nailgun user",
  :description  => "Nailgun daemon user",
  :default      => "vagrant"

