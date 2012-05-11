r = gem_package "httpclient" do
  action :nothing
end

r.run_action(:install)
Gem.clear_paths

require 'httpclient'

class Chef::Recipe
  include NodeAgent
end

send_ohai()
