require 'json'
require 'mcollective'

module Orchestrator
  class Orchestrator
  include MCollective::RPC

    private
    def check_mcollective_result(stats)
      stats.each do |agent|
        status = agent.results[:statuscode]
        raise "MCollective call failed in agent: #{agent}" unless status == 0
      end
    end

    public
    def deploy(nodes)
      # TODO Check if nodes contains all required data
      nodes.each do |node|
        mc = rpcclient("nailyfact")
        mc.progress = false
        mc.discover(:nodes => [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}
        stats = mc.post(:value => metadata.to_json)
        check_mcollective_result(stats)
      end

      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      mc = rpcclient("puppetd")
      mc.progress = false
      mc.discover(:nodes => macs)
      stats = mc.runonce
      check_mcollective_result(stats)
      printrpc mc.status
      sleep 5
      printrpc mc.status
    end

    def verify_networks(nodes, networks)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      mc = rpcclient("net_probe")
      mc.progress = false
      mc.discover(:nodes => macs)

      stats = mc.start_frame_listeners({'iflist' => 'eth0'})
      check_mcollective_result(stats)
      
      stats = mc.send_probing_frames({'interfaces' => {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}})
      check_mcollective_result(stats)

      sleep 5
      stats = mc.get_probing_info
      printrpc mc.get_probing_info
    end
  end

end
