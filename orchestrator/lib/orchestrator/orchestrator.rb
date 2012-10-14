module Orchestrator
  class Orchestrator
    include ::Orchestrator

    def initialize
      @deployer = method(:puppet_deploy_with_polling)
      @metapublisher = method(:publish_facts)
      @check_network = method(:check_network)
    end

    def deploy(reporter, task_id, nodes)
      context = Context.new(task_id, reporter)
      # Run actual deployment
      # First we deploy nodes with role 'controller'
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of controllers on nodes(macs): #{ctrl_nodes.map {|n| n['mac']}.join(',')}"
      
      # we post metadata so Puppet would know what to do when it starts
      @metapublisher.call(context, ctrl_nodes)
      reporter.report({'progress' => 1})
      @deployer.call(context, ctrl_nodes)
      reporter.report({'progress' => 40})

      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of computes on nodes(macs): #{compute_nodes.map {|n| n['mac']}.join(',')}"
      @metapublisher.call(context, compute_nodes)
      @deployer.call(context, compute_nodes)

      other_nodes = nodes - ctrl_nodes - compute_nodes
      ::Orchestrator.logger.info "#{task_id}: Starting deployment of other roles on nodes(macs): #{other_nodes.map {|n| n['mac']}.join(',')}"
      @metapublisher.call(context, other_nodes)
      @deployer.call(context, other_nodes)
      reporter.report({'progress' => 100})
    end

    def verify_networks(reporter, task_id, nodes, networks)
      context = Context.new(task_id, reporter)
      @check_network.call(context, nodes, networks)
    end
  end

end
