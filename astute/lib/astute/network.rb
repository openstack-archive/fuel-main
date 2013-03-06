module Astute
  module Network
    def self.check_network(ctx, nodes, networks)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Network checker: nodes list is empty. Nothing to check."
        return {'status' => 'error', 'error' => "Nodes list is empty. Nothing to check."}
      elsif nodes.size == 1
        Astute.logger.info "#{ctx.task_id}: Network checker: nodes list contains one node only. Do nothing."
        return {'nodes' =>
          [{'uid'=>nodes[0]['uid'],
            'networks'=>[{'vlans' => networks.map {|n| n['vlan_id'].to_i}, 'iface'=>'eth0'}]
          }]
        }
      end
      uids = nodes.map {|n| n['uid']}
      # TODO Everything breakes if agent not found. We have to handle that
      net_probe = MClient.new(ctx, "net_probe", uids)

      data_to_send = {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}
      net_probe.start_frame_listeners(:interfaces => data_to_send.to_json)
      ctx.reporter.report({'progress' => 30})

      # Interface name is hardcoded for now. Later we expect it to be passed from Nailgun backend
      data_to_send = {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}
      net_probe.send_probing_frames(:interfaces => data_to_send.to_json)
      ctx.reporter.report({'progress' => 60})

      stats = net_probe.get_probing_info
      result = stats.map {|node| {'uid' => node.results[:sender],
                                  'networks' => check_vlans_by_traffic(
                                            node.results[:sender],
                                            node.results[:data][:neighbours])} }
      Astute.logger.debug "#{ctx.task_id}: Network checking is done. Results: #{result.inspect}"
      {'nodes' => result}
    end

  private

    def self.check_vlans_by_traffic(uid, data)
      data.map do |iface, vlans|
        {
          'iface' => iface,
          'vlans' => vlans.reject{ |k, v|
            v.size == 1 && v.has_key?(uid)
          }.keys.map(&:to_i)
        }
      end
    end
  end
end
