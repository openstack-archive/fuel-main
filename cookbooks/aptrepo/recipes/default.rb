package "apt-utils" do
  action :install
end

reqdebs = node[:aptrepo][:reqdebs].join(' ')

template "/usr/bin/update_repo.sh" do
  source update_repo.sh.erb
  owner 'root'
  group 'root'
  mode 0755
  variables(
            :mirror => node[:aptrepo][:mirror],
            :release => node[:aptrepo][:release],
            :version => node[:aptrepo][:version],
            :reporoot => node[:aptrepo][:reporoot],
            :arch => node[:aptrepo][:arch],
            :reqdebs => reqdebs,
            :gnupghome => node[:aptrepo][:gnupghome],
            :gnupgkeyid => node[:aptrepo][:gnukeyid],
            :gnupgpasswdfile => node[:aptrepo][:gnupgpasswdfile]
            )
end

