#
# Cookbook Name:: mysql
# Recipe:: test
#
# Copyright 2008-2011, Keith Hudgins.
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

# This is a proof of concept/example for how to create a remote database
# Basically, you can use the snippets below

# Include OpenSSL Password so we can make a new password for our dbuser
# (This example re-uses)
::Chef::Recipe.send(:include, Opscode::OpenSSL::Password)

node.set_unless['testnamespace']['db_test_user_password']

include_recipe "mysql::client"

# Chef search query to pull your server. This returns an array
# of nodes. In our example here, there's only ONE mysql-server node. If,
# for some reason you have multiple notes with mysql-server role assigned
# via your barclamp, you'll need to adjust this.
# Because of this, we know it's the first one
# Thus, the db_server[0] bit.
db_server = search(:node, "fqdn:#{node['mysql-server']}")

# This saves the password so that we're idempotent.
# Doesn't work on chef solo since there's no place to 
# save node data there.
unless Chef::Config[:solo]
  ruby_block "save node data" do
    block do
      node.save
    end
    action :create
  end
end

mysql_database "create test database" do
  host "#{db_server[0].ipaddress}"
  username "db_maker"
  password "#{db_server[0].mysql.db_maker_password}"
  database "test_db"
  action :create_db
end

# This is a logging example of how to pull a password from the node's data space.
Chef::Log.info "pwgimme:  #{db_server[0].mysql.db_maker_password}"

mysql_database "create test database user" do
  host "#{db_server[0].ipaddress}"
  username "db_maker"
  password "#{db_server[0].mysql.db_maker_password}"
  database "test_db"
  action :query
  sql "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON *.* TO 'test_user'@'%' IDENTIFIED BY '#{node[:testnamespace][:db_test_user_password]}' WITH GRANT OPTION;"
end