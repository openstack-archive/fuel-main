#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe "DeploymentEngine" do
  context "When deploy is called, it" do
    before(:each) do
      @ctx = mock
      @deploy_engine = Astute::DeploymentEngine.new(@ctx)
    end

    it "should call valid method depends on attrs" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'ha_compute'}
      attrs_modified = attrs.merge({'some' => 'somea'})
      
      @deploy_engine.expects(:attrs_ha_compute).with(nodes, attrs).returns(attrs_modified)
      @deploy_engine.expects(:deploy_ha_compute).with(nodes, attrs_modified)
      # All implementations of deploy_piece go to subclasses
      @deploy_engine.respond_to?(:deploy_piece).should be_false
      @deploy_engine.deploy(nodes, attrs)
    end

    it "should raise an exception if deployment mode is unsupported" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'unknown'}
      expect {@deploy_engine.deploy(nodes, attrs)}.to raise_exception(/Method attrs_unknown is not implemented/)
    end
  end
end
