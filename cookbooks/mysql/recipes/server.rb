#
# Cookbook Name:: mysql
# Recipe:: default
#
# Copyright 2008-2011, Opscode, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


include_recipe "mysql::client"

if platform?(%w{debian ubuntu})

  directory "/var/cache/local/preseeding" do
    owner "root"
    group "root"
    mode 0755
    recursive true
  end

  template "/var/cache/local/preseeding/mysql-server.seed" do
    source "mysql-server.seed.erb"
    owner "root"
    group "root"
    mode "0600"
  end

  template "/etc/mysql/debian.cnf" do
    source "debian.cnf.erb"
    owner "root"
    group "root"
    mode "0600"
  end

  execute "preseed mysql-server" do
    command "debconf-set-selections /var/cache/local/preseeding/mysql-server.seed"
    only_if "test -f /var/cache/local/preseeding/mysql-server.seed" 
  end

end

# For Crowbar, we need to set the address to bind - default to admin node.
addr = node['mysql']['bind_address'] || ""
#newaddr = Chef::Recipe::Barclamp::Inventory.get_network_by_type(node, "admin").address
#if addr != newaddr
#  node['mysql']['bind_address'] = newaddr
#  node.save
#end

package "mysql-server" do
  action :install
end

service "mysql" do
  service_name value_for_platform([ "centos", "redhat", "suse", "fedora" ] => {"default" => "mysqld"}, "default" => "mysql")
  if (platform?("ubuntu") && node.platform_version.to_f >= 10.04)
    restart_command "restart mysql"
    stop_command "stop mysql"
    start_command "start mysql"
  end
  supports :status => true, :restart => true, :reload => true
  action :nothing
end

=begin
link value_for_platform([ "centos", "redhat", "suse" , "fedora" ] => {"default" => "/etc/my.cnf"}, "default" => "/etc/mysql/my.cnf") do
  to "#{node[:mysql][:datadir]}/my.cnf"
end
=end

directory node[:mysql][:tmpdir] do
  owner "mysql"
  group "mysql"
  mode "0700"
  action :create
end

directory node[:mysql][:logdir] do
  owner "mysql"
  group "mysql"
  mode "0700"
  action :create
end

script "handle mysql restart" do
  interpreter "bash"
  action :nothing
  code <<EOC
service mysql stop
rm /var/lib/mysql/ib_logfile?
service mysql start
EOC
end

template "#{node[:mysql][:datadir]}/my.cnf" do
  source "my.cnf.erb"
  owner "root"
  group "root"
  mode "0644"
  notifies :run, resources(:script => "handle mysql restart"), :immediately
end

unless Chef::Config[:solo]
  ruby_block "save node data" do
    block do
      node.save
    end
    action :create
  end
end

# set the root password on platforms 
# that don't support pre-seeding
unless platform?(%w{debian ubuntu})

  execute "assign-root-password" do
    command "/usr/bin/mysqladmin -u root password \"#{node['mysql']['server_root_password']}\""
    action :run
    only_if "/usr/bin/mysql -u root -e 'show databases;'"
  end

end

# Super duper hackfest-o-rama 2011.
# Under crowbar, for some reason, defaults aren't being set properly
# for the mysql passwords. This is a nasty, nasty hack to
# fix this until I understand the problem better:

template "/etc/mysql/conf.d/emergency_init_file" do
  source "emergency_init_file.erb"
  owner "root"
  group "root"
  mode "0600"
  action :create
end


script "fix_perms_hack" do
  interpreter "bash"
  user "root"
  cwd "/tmp"
  code <<-EOH
  /etc/init.d/mysql stop
  chmod 644 /etc/mysql/conf.d/emergency_init_file
  /usr/bin/mysqld_safe --init-file=/etc/mysql/conf.d/emergency_init_file &
  sleep 10
  killall mysqld
  chmod 600 /etc/mysql/conf.d/emergency_init_file
  /etc/init.d/mysql start
  EOH
  not_if "/usr/bin/mysql -u root #{node['mysql']['server_root_password'].empty? ? '' : '-p' }#{node['mysql']['server_root_password']} -e 'show databases;'"
end

# End hackness

grants_path = value_for_platform(
  ["centos", "redhat", "suse", "fedora" ] => {
    "default" => "/etc/mysql_grants.sql"
  },
  "default" => "/etc/mysql/grants.sql"
)

grants_key = value_for_platform(
  ["centos", "redhat", "suse", "fedora" ] => {
    "default" => "/etc/applied_grants"
  },
  "default" => "/etc/mysql/applied_grants"
)

template grants_path do
  source "grants.sql.erb"
  owner "root"
  group "root"
  mode "0600"
  action :create
  not_if { File.exists?("#{grants_key}") }
end

execute "mysql-install-privileges" do
  command "/usr/bin/mysql -u root #{node['mysql']['server_root_password'].empty? ? '' : '-p' }#{node['mysql']['server_root_password']} < #{grants_path}"
  action :nothing
  subscribes :run, resources("template[#{grants_path}]"), :immediately
end

file grants_path do
  backup false
  action :delete
end

file grants_key do
  owner "root"
  group "root"
  mode "0600"
  action :create_if_missing
end
