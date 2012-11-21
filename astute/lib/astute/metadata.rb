require 'json'
require 'ipaddr'

module Astute
  module Metadata
    def self.publish_facts(ctx, nodes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to post metadata into are not provided. Do nothing."
        return false
      end
      uids = nodes.map {|n| n['uid']}
      Astute.logger.debug "#{ctx.task_id}: nailyfact - storing metadata for nodes: #{uids.join(',')}"

      nodes.each do |node|
        nailyfact = MClient.new(ctx, "nailyfact", [node['uid']])
        intfhash = Hash.new do |hash, key|
            hash[key] = {}
        end
        node['network_data'].each do |intf|
            intfhash[intf['dev']]=intf
            ipmask=intf['ip'].split('/')
            intfhash[intf['dev']]['ip']=ipmask[0]
            intfhash[intf['dev']]['mask']=IPAddr.new('255.255.255.255').mask(ipmask[1]).to_s
        end
        metadata = {'role' => node['role'], 'id' => node['id'], 'uid' => node['uid'], 'network_data' => intfhash.to_json }

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = nailyfact.post(:value => metadata.to_json)
      end
    end
  end
end
