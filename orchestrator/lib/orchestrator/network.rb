module Orchestrator
  class Network
    include MCollective::RPC
    include ::Orchestrator

    def check_network(reporter, task_id, nodes, networks)
      if nodes.length < 2
        ::Orchestrator.logger.info "#{task_id}: Network checker: at least two nodes are required to check network connectivity. Do nothing."
        return false
      end
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      # TODO Everything breakes if agent not found. We have to handle that
      mc = rpcclient("net_probe")
      mc.progress = false
      mc.discover(:nodes => macs)

      stats = mc.start_frame_listeners(:iflist => ['eth0'].to_json)
      check_mcollective_result(stats, task_id)
      
      # Interface is hardcoded for now. Later we expect it to be passed from Nailgun backend
      data_to_send = {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}
      stats = mc.send_probing_frames(:interfaces => data_to_send.to_json)
      check_mcollective_result(stats, task_id)

      stats = mc.get_probing_info
      # TODO return result like [ {'node' => 'id_of_node', 'network' => [ {'iface' => 'eth0', 'vlan' => [100,101]} } ]
      p stats
    end
  end
end
