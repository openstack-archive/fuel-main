# NOTE(mihgen): this file is modified copy of puppet's indirector/node/exec.rb
require 'puppet/node'
require 'puppet/indirector/exec'

# It must be configured in puppet.conf (or passed in cmdline) 'node_terminus = exec' to make use of it
class Puppet::Node::Exec < Puppet::Indirector::Exec
  desc "Obtain information about node from our orchestrator - Astute"
  include Puppet::Util

  # Look for external node definitions.
  def find(request)
    node = Puppet::Node.new(request.key)

    result = Astute.get_config
    Puppet.info("Obtained configuration from Astute: #{result.inspect}")

    %w{parameters classes environment}.each do |param|
      if value = result[param]
        node.send(param.to_s + "=", value)
      end
    end

    node.fact_merge
    node
  end

end
