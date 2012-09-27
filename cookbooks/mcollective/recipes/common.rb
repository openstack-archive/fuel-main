#
# Cookbook Name:: mcollective
# Recipe:: common
#
# Resources required by both client and server.
#
# Copyright 2011, Zachary Stevens
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

package "rubygems" do
  action :install
end

package "rubygem-stomp" do
  case node['platform']
  when "ubuntu","debian"
    package_name "libstomp-ruby"
  when "centos","redhat","fedora"
    package_name "rubygem-stomp"
  end
  action :install
end

package "mcollective-common" do
  action :install
end
