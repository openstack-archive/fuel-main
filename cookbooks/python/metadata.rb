maintainer       "Mirantis Inc."
maintainer_email "product@mirantis.com"
license          "Apache 2.0"
description      "Installs python"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.rdoc'))
version          "0.0.1"
supports         "ubuntu", "= 12.04"
recipe           "python", "Installs python itself"

