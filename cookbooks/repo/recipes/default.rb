package "apt-utils" do
  action :install
end

reqdebs = node[:repo][:reqdebs].join(' ')

template "/usr/bin/update_repo.sh" do
  source update_repo.sh.erb
  owner 'root'
  group 'root'
  mode 0755
  variables(
            :mirror => node[:repo][:mirror],
            :release => node[:repo][:release],
            :version => node[:repo][:version],
            :reporoot => node[:repo][:reporoot],
            :arch => node[:repo][:arch],
            :reqdebs => reqdebs,
            :gnupghome => node[:repo][:gnupghome],
            :gnupgkeyid => node[:repo][:gnukeyid],
            :gnupgpasswdfile => node[:repo][:gnupgpasswdfile]
            )
end

