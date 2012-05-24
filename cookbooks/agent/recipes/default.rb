chef_gem 'httpclient'

require 'httpclient'

ruby_block 'update_node_info' do
  block { NodeAgent.update(node) }
end

