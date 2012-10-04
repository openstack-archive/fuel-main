
gem_package 'naily'

user  node[:naily][:user]
group node[:naily][:group]

template '/etc/init.d/naily' do
  source 'sv-init.erb'
  mode '0755'
end

directory '/etc/naily' do
  owner node[:naily][:user]
  group node[:naily][:group]
  mode '0755'
end

template '/etc/naily/nailyd.conf' do
  owner node[:naily][:user]
  group node[:naily][:group]
  mode '0644'
end

service 'naily' do
  action [:enable, :start]
end

