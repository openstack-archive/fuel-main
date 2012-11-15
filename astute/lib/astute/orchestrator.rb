module Astute
  class Orchestrator
    def initialize
      @deployer = Astute::Deployer.method(:puppet_deploy_with_polling)
      @metapublisher = Astute::Metadata.method(:publish_facts)
      @check_network = Astute::Network.method(:check_network)
    end

    def node_type(reporter, task_id, nodes)
      context = Context.new(task_id, reporter)
      uids = nodes.map {|n| n['uid']}
      systemtype = MClient.new(context, "systemtype", uids, check_result=false)
      systems = systemtype.get_type
      return systems.map {|n| {'uid' => n.results[:sender], 'node_type' => n.results[:data][:node_type].chomp}}
    end

    def deploy(reporter, task_id, nodes)
      context = Context.new(task_id, reporter)

      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      deploy_piece(context, ctrl_nodes)
      reporter.report({'progress' => 40})

      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      deploy_piece(context, compute_nodes)
      reporter.report({'progress' => 60})

      other_nodes = nodes - ctrl_nodes - compute_nodes
      deploy_piece(context, other_nodes)
      return
    end

    def remove_nodes(reporter, task_id, nodes)
      context = Context.new(task_id, reporter)
      result = simple_remove_nodes(context, nodes)
      return result
    end

    def verify_networks(reporter, task_id, nodes, networks)
      context = Context.new(task_id, reporter)
      result = @check_network.call(context, nodes, networks)
      if result.empty?
        return {'status' => 'error', 'error' => "At least two nodes are required to check network connectivity."}
      end

      result.map! { |node| {'uid' => node['sender'],
                            'networks' => check_vlans_by_traffic(node['sender'], node['data'][:neighbours]) }
                  }
      return {'networks' => result}
    end

    private
    def simple_remove_nodes(ctx, nodes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to remove are not provided. Do nothing."
        return {'nodes' => nodes}
      end
      uids = nodes.map {|n| n['uid'].to_s}
      Astute.logger.info "#{ctx.task_id}: Starting removing of nodes: #{uids.inspect}"
      remover = MClient.new(ctx, "erase_node", uids, check_result=false)
      result = remover.erase_node(:reboot => true)
      Astute.logger.debug "#{ctx.task_id}: Data resieved from nodes: #{result.inspect}"
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

    def deploy_piece(ctx, nodes)
      nodes_roles = nodes.map { |n| { n['uid'] => n['role'] } }
      Astute.logger.info "#{ctx.task_id}: Starting deployment of nodes => roles: #{nodes_roles.inspect}"
      ctx.reporter.report nodes_status(nodes, 'deploying')
      @metapublisher.call(ctx, nodes)
      @deployer.call(ctx, nodes)
      ctx.reporter.report nodes_status(nodes, 'ready')
      Astute.logger.info "#{ctx.task_id}: Finished deployment of nodes => roles: #{nodes_roles.inspect}"
    end

    def nodes_status(nodes, status)
      {'nodes' => nodes.map { |n| {'uid' => n['uid'], 'status' => status} }}
    end

    def check_vlans_by_traffic(uid, data)
      return data.map{|iface, vlans| {'iface' => iface, 'vlans' => vlans.reject{|k,v| v.size==1 and v.has_key?(uid)}.keys.map{|n| n.to_i} } }
    end
  end
end
