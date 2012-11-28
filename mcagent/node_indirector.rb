# NOTE(mihgen): this file is modified copy of puppet's indirector/node/exec.rb
# See more about node terminus here: http://rcrowley.org/talks/sv-puppet-2011-01-11/#47
# and http://www.masterzen.fr/2011/12/11/the-indirector-puppet-extensions-points-3/
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
