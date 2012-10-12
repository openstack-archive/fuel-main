require 'set'

module Orchestrator
  class Orchestrator

    def initialize
      @deployer = PuppetDeployer.new
      @metapublisher = FactsPublisher.new
    end

    def deploy(reporter, task_id, nodes)

      # Run actual deployment
      # First we deploy nodes with role 'controller'
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of controllers on nodes(macs): #{ctrl_nodes.map {|n| n['mac']}.join(',')}"
      
      # we post metadata so Puppet would know what to do when it starts
      @metapublisher.post(reporter, task_id, ctrl_nodes)
      reporter.report({'progress' => 1})
      @deployer.deploy(reporter, task_id, ctrl_nodes)
      reporter.report({'progress' => 40})

      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of computes on nodes(macs): #{compute_nodes.map {|n| n['mac']}.join(',')}"
      @metapublisher.post(reporter, task_id, compute_nodes)
      @deployer.deploy(reporter, task_id, compute_nodes)

      other_nodes = (nodes.to_set - ctrl_nodes.to_set - compute_nodes.to_set).to_a
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of other roles on nodes(macs): #{other_nodes.map {|n| n['mac']}.join(',')}"
      @metapublisher.post(reporter, task_id, other_nodes)
      @deployer.deploy(reporter, task_id, other_nodes)
    end

    # TODO rewrite it in a new model
    #def verify_networks(reporter, task_id, nodes, networks)
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
