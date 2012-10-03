package "puppetmaster"

service "puppetmaster" do
  action [:enable]
end

template "/etc/puppet/puppet.conf" do
  source 'puppet.conf.erb'
  mode '644'
  notifies :restart, service['puppetmaster']
end

service "puppetmaster" do
  action [:start]
end
