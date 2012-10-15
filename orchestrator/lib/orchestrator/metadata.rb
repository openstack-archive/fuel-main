require 'json'

module Orchestrator
  def publish_facts(ctx, nodes)
    if nodes.empty?
      ::Orchestrator.logger.info "#{ctx.task_id}: Nodes to post metadata into are not provided. Do nothing."
      return false
    end
    macs = nodes.map {|n| n['mac'].gsub(":", "")}
    ::Orchestrator.logger.debug "#{ctx.task_id}: nailyfact - storing metadata for nodes: #{macs.join(',')}"

    nodes.each do |node|
      nailyfact = MClient.new(ctx, "nailyfact", [node['mac'].gsub(":", "")])
      metadata = {'role' => node['role']}

      # This is synchronious RPC call, so we are sure that data were sent and processed remotely
      stats = nailyfact.post(:value => metadata.to_json)
    end
  end
end
