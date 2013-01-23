module Astute
  module Network
    def self.check_network(ctx, nodes, networks)
      if nodes.empty?
        Astute.logger.error "#{ctx.task_id}: Network checker: nodes list is empty. Nothing to check."
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

      net_probe.start_frame_listeners(:iflist => ['eth0'].to_json)
      ctx.reporter.report({'progress' => 30, 'status' => 'verification'})
      
      # Interface name is hardcoded for now. Later we expect it to be passed from Nailgun backend
      data_to_send = {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}
      net_probe.send_probing_frames(:interfaces => data_to_send.to_json)
      ctx.reporter.report({'progress' => 60, 'status' => 'verification'})

      stats = net_probe.get_probing_info
      result = stats.map {|node| {'sender' => node.results[:sender], 'data' => node.results[:data]} }
      Astute.logger.debug "#{ctx.task_id}: Network checking is done. Raw results: #{result.inspect}"
      result.map! { |node| {'uid' => node['sender'],
                            'networks' => check_vlans_by_traffic(node['sender'], node['data'][:neighbours]) }
                  }
      return {'nodes' => result}
    end

    private
    def self.check_vlans_by_traffic(uid, data)
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
