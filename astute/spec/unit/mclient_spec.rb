#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")
include Astute

describe "MCollectiveClient" do
  context "When MClient is instantiated" do
    it "it should receive method call and process valid result correctly" do
      @ctx = mock
      @ctx.stubs(:task_id)
      @ctx.stubs(:reporter)
      nodes = [1, 2, 3]
      rpcclient = mock
      rpcclient.stubs(:progress=)
      nodes_to_discover = nodes.map { |n| n.to_s }
      rpcclient.expects(:discover).with(:nodes => nodes_to_discover).once #.returns(["foo"])
      rpcclient_valid_result = mock
      rpcclient_valid_result.stubs(:results).returns(
          {:statuscode=>0, :statusmsg=>"OK", :data=>{
                :stopped=>1, :status=>"stopped", :lastrun=>1356502406, :output=>"text msg",
                :enabled=>1, :idling=>0, :running=>0}, :sender=>"1"})
      rpcclient_valid_result.stubs(:agent).returns('faketest')

      rpcclient.expects(:echo).with(:msg => 'hello world').once.returns([rpcclient_valid_result]*3)
      
      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      
      mclient = MClient.new(@ctx, "faketest", nodes)
      stats = mclient.echo(:msg => 'hello world')
      stats.should eql([rpcclient_valid_result]*3)
    end

  end
end
