module Astute
  class Orchestrator
    def initialize
      @deployer = Astute::Deployer.method(:puppet_deploy_with_polling)
      @metapublisher = Astute::Metadata.method(:publish_facts)
      @check_network = Astute::Network.method(:check_network)
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

    def verify_networks(reporter, task_id, nodes, networks)
      context = Context.new(task_id, reporter)
      result = @check_network.call(context, nodes, networks)
      result.map! { |node| {'uid' => node['sender'],
                            'networks' => check_vlans_by_traffic(node['data'][:neighbours]) }
                  }
      return {'networks' => result}
    end

    private
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

    def check_vlans_by_traffic(data)
      return data.map{|iface, vlans| {'iface' => iface, 'vlans' => vlans.keys.map{|n| n.to_i} } }
    end
  end
end
