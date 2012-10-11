module Orchestrator
  class Orchestrator

    def initialize
      @deployer = PuppetDeployer.new
      @metapublisher = FactsPublisher.new
    end

    def deploy(reporter, nodes)
      # First we post metadata so Puppet would know it when it starts
      @metapublisher.post(reporter, nodes)
      reporter.report({'progress' => 1})

      # Run actual deployment
      @deployer.deploy(reporter, nodes)
    end

    # TODO rewrite it in a new model
    #def verify_networks(reporter, nodes, networks)
      #macs = nodes.map {|n| n['mac'].gsub(":", "")}
      #mc = rpcclient("net_probe")
      #mc.progress = false
      #mc.discover(:nodes => macs)

      #stats = mc.start_frame_listeners({'iflist' => 'eth0'})
      #check_mcollective_result(stats)
      
      #stats = mc.send_probing_frames({'interfaces' => {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}})
      #check_mcollective_result(stats)

      #sleep 5
      #stats = mc.get_probing_info
      #printrpc mc.get_probing_info
    #end
  end

end
