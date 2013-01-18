module Astute
  class Orchestrator
    def initialize(deploy_engine=nil)
      @deploy_engine = deploy_engine ||= Astute::DeploymentEngine::NailyFact
      @check_network = Astute::Network.method(:check_network)
    end

    def node_type(reporter, task_id, nodes, timeout=nil)
      context = Context.new(task_id, reporter)
      uids = nodes.map {|n| n['uid']}
      systemtype = MClient.new(context, "systemtype", uids, check_result=false, timeout)
      systems = systemtype.get_type
      return systems.map {|n| {'uid' => n.results[:sender], 'node_type' => n.results[:data][:node_type].chomp}}
    end

    def deploy(reporter, task_id, nodes, attrs)
      raise "Nodes to deploy are not provided!" if nodes.empty?
      # Following line fixes issues with uids: it should always be string
      nodes.map { |x| x['uid'] = x['uid'].to_s }
      context = Context.new(task_id, reporter)
      deploy_engine_instance = @deploy_engine.new(context)
      deploy_engine_instance.deploy(nodes, attrs)
    end

    def remove_nodes(reporter, task_id, nodes)
      context = Context.new(task_id, reporter)
      result = simple_remove_nodes(context, nodes)
      return result
    end

    def verify_networks(reporter, task_id, nodes, networks)
      if nodes.empty?
        Astute.logger.error "#{task_id}: Network checker: nodes list is empty. Nothing to check."
        return {'status' => 'error', 'error' => "Nodes list is empty. Nothing to check."}
      elsif nodes.size == 1
        Astute.logger.info "#{task_id}: Network checker: nodes list contains one node only. Do nothing."
        return {'nodes' =>
          [{'uid'=>nodes[0]['uid'],
            'networks'=>[{'vlans' => networks.map {|n| n['vlan_id'].to_i}, 'iface'=>'eth0'}]
          }]
        }
      end

      context = Context.new(task_id, reporter)
      result = @check_network.call(context, nodes, networks)
      result.map! { |node| {'uid' => node['sender'],
                            'networks' => check_vlans_by_traffic(node['sender'], node['data'][:neighbours]) }
                  }
      return {'nodes' => result}
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

    def check_vlans_by_traffic(uid, data)
      return data.map{|iface, vlans| {
        'iface' => iface,
        'vlans' =>
          vlans.reject{|k,v|
            v.size==1 and v.has_key?(uid)
          }.keys.map{|n| n.to_i}
        }
      }
    end
  end
end
