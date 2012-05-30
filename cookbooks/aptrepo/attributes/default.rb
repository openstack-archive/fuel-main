default[:aptrepo][:reqdebs] = ['chef', 
                               'cobbler', 
                               'cobbler-web', 
                               'dnsmasq', 
                               'tftpd-hpa', 
                               'apt-utils']
default[:aptrepo][:mirror] = 'http://archive.ubuntu.com/ubuntu'
default[:aptrepo][:release] = 'precise'
default[:aptrepo][:version] = '12.04'
default[:aptrepo][:reporoot] = '/var/lib/mirror/ubuntu'
default[:aptrepo][:arch] = 'amd64'
default[:aptrepo][:gnupghome] = '/root/.gnupg'
default[:aptrepo][:gnupgkeyid] = 'F8AF89DD'
default[:aptrepo][:gnupgpasswdfile] = '/root/.gnupg/keyphrase'

