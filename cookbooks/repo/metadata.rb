maintainer        "Mirantis, Inc."
maintainer_email  "product@mirantis.com"
description       "Installs and configures cobbler"
version           "0.0.1"
recipe            "repo::default", "Creates script to update ubuntu repo"
recipe            "repo::http", "Creates apache2 site to publish ubuntu repo"
supports          "ubuntu"

