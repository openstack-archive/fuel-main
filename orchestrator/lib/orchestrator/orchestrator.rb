require 'set'

module Orchestrator
  class Orchestrator

    def initialize
      @deployer = PuppetPollingDeployer.new
      @metapublisher = FactsPublisher.new
      @network = Network.new
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
      reporter.report({'progress' => 100})
    end

    def verify_networks(reporter, task_id, nodes, networks)
      @network.check_network(reporter, task_id, nodes, networks)
    end
  end

end
