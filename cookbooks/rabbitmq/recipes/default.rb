#
# Cookbook Name:: rabbitmq
# Recipe:: default
#
# Copyright 2009, Benjamin Black
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

package "rabbitmq-server"

service "rabbitmq-server" do
  action [ :enable ]
end

template "/etc/rabbitmq/rabbitmq.config" do
  source "rabbitmq.config.erb"
  mode 0644
  notifies :restart, resources(:service => "rabbitmq-server")
end

cookbook_file "/etc/rabbitmq/enabled_plugins" do
  source "enabled_plugins"
  mode 0644
  notifies :restart, resources(:service => "rabbitmq-server")
end

service "rabbitmq-server" do
  action [ :start ]
end
