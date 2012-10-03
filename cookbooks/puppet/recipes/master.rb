package "puppetmaster"

service "puppetmaster" do
  action [:enable]
  pattern "puppet master"
end

template "/etc/puppet/puppet.conf" do
  source 'puppet.conf.erb'
  mode '644'
  notifies :restart, "service[puppetmaster]"
end

service "puppetmaster" do
  action [:start]
  pattern "puppet master"
end
