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
      attrs = {'deployment_mode' => 'ha_compute'}
      @deploy_engine.expects(:attrs_ha_compute).never  # It is not supported in SimplePuppet
      @deploy_engine.expects(:deploy_ha_compute).with(nodes, attrs)
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

    it "multinode_compute deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "multinode_compute"
      Astute::Metadata.expects(:publish_facts).never  # It is not supported in SimplePuppet
      # we got two calls, one for controller, and another for all computes
      Astute::PuppetdDeployer.expects(:deploy).twice
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "ha_compute deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "ha_compute"
      Astute::Metadata.expects(:publish_facts).never
      Astute::PuppetdDeployer.expects(:deploy).times(6)
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end

    it "singlenode_compute deploy should not raise any exception" do
      @env['attributes']['deployment_mode'] = "singlenode_compute"
      @env['nodes'] = [@env['nodes'][0]]  # We have only one node in singlenode
      Astute::Metadata.expects(:publish_facts).never
      Astute::PuppetdDeployer.expects(:deploy).once  # one call for one node
      @deploy_engine.deploy(@env['nodes'], @env['attributes'])
    end
  end
end
