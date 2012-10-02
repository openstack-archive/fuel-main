require File.join(File.dirname(__FILE__), "..", "spec_helper")
require 'mcollective'
include MCollective::RPC

describe "MCollective" do
context "When MC agent is up and running" do
  it "it should send echo message to MC agent and get it back" do
    node = "admin"
    data_to_send = "simple message of node '#{node}'"
    mc = rpcclient("fake")
    mc.progress = false
    mc.discover(:nodes => [node])
    stats = mc.echo(:msg => data_to_send)
    stats.should have(1).items
    stats[0].results[:statuscode].should eql(0)
    stats[0].results[:data][:msg].should eql("Hello, it is my reply: #{data_to_send}")
  end

  it "it should update facts file with new key-value and could get it back" do
    value_to_send = rand(2**30).to_s
    node = "admin"
    mc = rpcclient("nailyfact")
    mc.progress = false
    mc.discover(:nodes => [node])
    stats = mc.put(:key => "role", :value => value_to_send)
    stats.should have(1).items
    stats[0].results[:statuscode].should eql(0)
    stats = mc.get(:key => "role")
    stats.should have(1).items
    stats[0].results[:statuscode].should eql(0)
    stats[0].results[:data][:value].should eql(value_to_send)
  end
end
end
