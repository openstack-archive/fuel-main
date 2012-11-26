require 'puppet/node'
require 'puppet/indirector/exec'

class Puppet::Node::Exec < Puppet::Indirector::Exec
  desc "Call an external program to get node information.  See
  the [External Nodes](http://docs.puppetlabs.com/guides/external_nodes.html) page for more information."
  include Puppet::Util

  # Look for external node definitions.
  def find(request)
    puts "******************************************* HERE HERE HERE HERE *****************************"
    node = Puppet::Node.new(request.key)
    result = Astute.get_config
    %w{parameters classes environment}.each do |param|
      if value = result[param]
        node.send(param.to_s + "=", value)
      end
    end

    node.fact_merge
    node
  end

end
