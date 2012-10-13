require 'json'

module Orchestrator
  class FactsPublisher
    include ::Orchestrator

    def post(ctx, nodes)
      if nodes.empty?
        ::Orchestrator.logger.info "#{ctx.task_id}: Nodes to post metadata into are not provided. Do nothing."
        return false
      end
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      ::Orchestrator.logger.debug "#{ctx.task_id}: nailyfact - storing metadata for nodes: #{macs.join(',')}"

      nodes.each do |node|
        mc = MClient.new(ctx, "nailyfact", [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = mc.post(:value => metadata.to_json)
      end
    end
  end
end
