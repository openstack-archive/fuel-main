require 'json'

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
        metadata = {'role' => node['role']}

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = nailyfact.post(:value => metadata.to_json)
      end
    end
  end
end
