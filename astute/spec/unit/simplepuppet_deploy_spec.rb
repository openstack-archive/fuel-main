#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe "SimplePuppet DeploymentEngine" do
  context "When deploy is called, " do
    before(:each) do
      @ctx = mock
      @ctx.stubs(:task_id)
      @ctx.stubs(:deploy_log_parser).returns(Astute::LogParser::NoParsing.new)
      @reporter = mock('reporter')
      @reporter.stub_everything
      @ctx.stubs(:reporter).returns(Astute::ProxyReporter.new(@reporter))
      @deploy_engine = Astute::DeploymentEngine::SimplePuppet.new(@ctx)
      @env = YAML.load_file(File.join(File.dirname(__FILE__), "..", "..", "examples", "no_attrs.yaml"))
    end

    it "it should call valid method depends on attrs" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'ha'}
      @deploy_engine.expects(:attrs_ha).never  # It is not supported in SimplePuppet
      @deploy_engine.expects(:deploy_ha).with(nodes, attrs)
      # All implementations of deploy_piece go to subclasses
      @deploy_engine.respond_to?(:deploy_piece).should be_true
      @deploy_engine.deploy(nodes, attrs)
    end

    it "it should raise an exception if deployment mode is unsupported" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'unknown'}
      expect {@deploy_engine.deploy(nodes, attrs)}.to raise_exception(
              /Method deploy_unknown is not implemented/)
    end

    it "multinode deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "multinode"
      Astute::Metadata.expects(:publish_facts).never  # It is not supported in SimplePuppet
      # we got two calls, one for controller, and another for all computes
      Astute::PuppetdDeployer.expects(:deploy).twice
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "ha deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "ha"
      Astute::Metadata.expects(:publish_facts).never
      Astute::PuppetdDeployer.expects(:deploy).times(6)
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "singlenode deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "singlenode"
      @env['nodes'] = [@env['nodes'][0]]  # We have only one node in singlenode
      Astute::Metadata.expects(:publish_facts).never
      Astute::PuppetdDeployer.expects(:deploy).once  # one call for one node
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "ha_compact deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "ha_compact"
      @env['nodes'].concat([{'uid'=>'c1', 'role'=>'controller'},
                            {'uid'=>'c2', 'role'=>'controller'},
                            {'uid'=>'o1', 'role'=>'other'}])
      controller_nodes = @env['nodes'].select{|n| n['role'] == 'controller'}
      compute_nodes = @env['nodes'].select{|n| n['role'] == 'compute'}
      other_nodes = @env['nodes'] - controller_nodes - compute_nodes

      Astute::Metadata.expects(:publish_facts).never
      controller_nodes.each do |n|
        Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [n], 0, false).once
      end
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [controller_nodes.first], 0, false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes[1..-1], 0, false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [controller_nodes.first], 0, true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes[1..-1], 0, true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, other_nodes, instance_of(Fixnum), true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, compute_nodes, instance_of(Fixnum), true).once
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "ha_full deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "ha_full"
      @env['nodes'].concat([{'uid'=>'c1', 'role'=>'controller'}, {'uid'=>'c2', 'role'=>'controller'},
                            {'uid'=>'q1', 'role'=>'quantum'}, {'uid'=>'q2', 'role'=>'quantum'},
                            {'uid'=>'st1', 'role'=>'storage'}, {'uid'=>'st2', 'role'=>'storage'},
                            {'uid'=>'sw1', 'role'=>'swift-proxy'}, {'uid'=>'sw2', 'role'=>'swift-proxy'},
                            {'uid'=>'o1', 'role'=>'other'}])
      controller_nodes = @env['nodes'].select{|n| n['role'] == 'controller'}
      compute_nodes = @env['nodes'].select{|n| n['role'] == 'compute'}
      quantum_nodes = @env['nodes'].select {|n| n['role'] == 'quantum'}
      storage_nodes = @env['nodes'].select {|n| n['role'] == 'storage'}
      proxy_nodes = @env['nodes'].select {|n| n['role'] == 'swift-proxy'}
      other_nodes = @env['nodes'] - controller_nodes - compute_nodes - quantum_nodes - storage_nodes -proxy_nodes

      Astute::Metadata.expects(:publish_facts).never
      controller_nodes.each do |n|
        Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [n], 0, true).once
      end
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [controller_nodes.first], 0, true).once

      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, quantum_nodes, 0, true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, compute_nodes, instance_of(Fixnum), true).once

      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, storage_nodes, instance_of(Fixnum), false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, storage_nodes, instance_of(Fixnum), false).once

      proxy_nodes.each do |n|
        Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [n], 0, false).once
      end

      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, storage_nodes, instance_of(Fixnum), true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, proxy_nodes, instance_of(Fixnum), true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, other_nodes, instance_of(Fixnum), true).once
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end
  end
end
