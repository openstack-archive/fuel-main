default[:repo][:reqdebs] = ['chef', 
                               'cobbler', 
                               'cobbler-web', 
                               'dnsmasq', 
                               'tftpd-hpa', 
                               'apt-utils']
default[:repo][:mirror] = 'http://archive.ubuntu.com/ubuntu'
default[:repo][:release] = 'precise'
default[:repo][:version] = '12.04'
default[:repo][:reporoot] = '/var/lib/mirror/ubuntu'
default[:repo][:arch] = 'amd64'
default[:repo][:gnupghome] = '/root/.gnupg'
default[:repo][:gnupgkeyid] = 'F8AF89DD'
default[:repo][:gnupgpasswdfile] = '/root/.gnupg/keyphrase'

default[:repo][:ubuntu][:root] = '/var/lib/mirror/ubuntu'
default[:repo][:centos][:root] = '/var/lib/mirror/centos'
default[:repo][:gems][:root] = '/var/lib/mirror/gems'
