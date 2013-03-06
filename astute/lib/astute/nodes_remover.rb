module Astute
  class NodesRemover

    def initialize(ctx, nodes)
      @ctx = ctx
      @nodes = NodesHash.build(nodes)
    end

    def remove
      # TODO(mihgen):  1. Nailgun should process node error message
      #   2. Should we rename nodes -> removed_nodes array?
      #   3. If exception is raised here, we should not fully fall into error, but only failed node
      erased_nodes, error_nodes, inaccessible_nodes = remove_nodes(@nodes)
      error_nodes.merge! inaccessible_nodes
      retry_remove_nodes error_nodes, erased_nodes, Astute.config[:MC_RETRIES], Astute.config[:MC_RETRY_INTERVAL]
      if error_nodes.empty?
        answer = {'nodes' => erased_nodes.nodes.map(&:to_hash)}
      else
        answer = {'status' => 'error', 'nodes' => erased_nodes.nodes.map(&:to_hash), 'error_nodes' => error_nodes.nodes.map(&:to_hash)}
        Astute.logger.error "#{@ctx.task_id}: Removing of nodes #{@nodes.uids.inspect} finished "\
                                             "with errors: #{error_nodes.nodes.inspect}"
      end
      Astute.logger.info "#{@ctx.task_id}: Finished removing of nodes: #{@nodes.uids.inspect}"
      answer
    end

  private

    def remove_nodes(nodes)
      if nodes.empty?
        Astute.logger.info "#{@ctx.task_id}: Nodes to remove are not provided. Do nothing."
        return Array.new(3){ NodesHash.new }
      end
      Astute.logger.info "#{@ctx.task_id}: Starting removing of nodes: #{nodes.uids.inspect}"
      remover = MClient.new(@ctx, "erase_node", nodes.uids.sort, check_result=false)
      responses = remover.erase_node(:reboot => true)
      Astute.logger.debug "#{@ctx.task_id}: Data received from nodes: #{responses.inspect}"
      inaccessible_uids = nodes.uids - responses.map{|response| response.results[:sender] }
      inaccessible_nodes = NodesHash.build(inaccessible_uids.map do |uid|
        {'uid' => uid, 'error' => 'Node not answered by RPC.'}
      end)
      error_nodes = NodesHash.new
      erased_nodes = NodesHash.new
      responses.each do |response|
        node = Node.new('uid' => response.results[:sender])
        if response.results[:statuscode] != 0
          node['error'] = "RPC agent 'erase_node' failed. Result: #{response.results.inspect}"
          error_nodes << node
        elsif not response.results[:data][:rebooted]
          node['error'] = "RPC method 'erase_node' failed with message: #{response.results[:data][:error_msg]}"
          error_nodes << node
        else
          erased_nodes << node
        end
      end
      [erased_nodes, error_nodes, inaccessible_nodes]
    end

    def retry_remove_nodes(error_nodes, erased_nodes, retries=3, interval=1)
      until retries == 0
        retries -= 1
        retried_erased_nodes = remove_nodes(error_nodes)[0]
        retried_erased_nodes.each do |uid, node|
          error_nodes.delete uid
          erased_nodes << node
        end
        return if error_nodes.empty?
        sleep interval if interval > 0
      end
    end
  end
end
