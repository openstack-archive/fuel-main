# It is assumed that httpclient gem
# already installed by preseed
require 'httpclient'

ruby_block 'update_node_info' do
  block { NodeAgent.update(node) }
end

