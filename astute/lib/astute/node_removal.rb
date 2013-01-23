module Astute
  class NodeRemoval
    def remove(ctx, nodes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to remove are not provided. Do nothing."
        return {'nodes' => []}
      end
      uids = nodes.map {|n| n['uid'].to_s}
      Astute.logger.info "#{ctx.task_id}: Starting removing of nodes: #{uids.inspect}"
      remover = MClient.new(ctx, "erase_node", uids, check_result=false)
      result = remover.erase_node(:reboot => true)
      Astute.logger.debug "#{ctx.task_id}: Data received from nodes: #{result.inspect}"
      inaccessible_uids = uids - result.map {|n| n.results[:sender]}
      error_nodes = []
      erased_nodes = []
      result.each do |n|
        if n.results[:statuscode] != 0
          error_nodes << {'uid' => n.results[:sender],
                         'error' => "RPC agent 'erase_node' failed. Result: #{n.results.inspect}"}
        elsif not n.results[:data][:rebooted]
          error_nodes << {'uid' => n.results[:sender],
                         'error' => "RPC method 'erase_node' failed with message: #{n.results[:data][:error_msg]}"}
        else
          erased_nodes << {'uid' => n.results[:sender]}
        end
      end
      error_nodes.concat(inaccessible_uids.map {|n| {'uid' => n, 'error' => "Node not answered by RPC."}})
      if error_nodes.empty?
        answer = {'nodes' => erased_nodes}
      else
        answer = {'status' => 'error', 'nodes' => erased_nodes, 'error_nodes' => error_nodes}
        Astute.logger.error "#{ctx.task_id}: Removing of nodes #{uids.inspect} ends with errors: #{error_nodes.inspect}"
      end
      Astute.logger.info "#{ctx.task_id}: Finished removing of nodes: #{uids.inspect}"
      return answer
    end
  end
end
