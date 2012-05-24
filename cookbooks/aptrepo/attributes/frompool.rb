default["aptrepo"]["architectures"] = ["i386", "amd64"]
default["aptrepo"]["sections"] = ["main", "restricted", "extras"]
default["aptrepo"]["release"] = "precise"
default["aptrepo"]["version"] = "12.04"
default["aptrepo"]["reporoot"] = "/var/lib/mirror/ubuntu"
default["aptrepo"]["repoindices"] = "#{default["aptrepo"]["reporoot"]}/indices" 
default["aptrepo"]["repocache"] = "#{default["aptrepo"]["reporoot"]}/cache" 
default["aptrepo"]["repoconf.d"] = "/var/lib/mirror/ubuntu-conf.d"
