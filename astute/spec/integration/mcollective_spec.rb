require File.join(File.dirname(__FILE__), "..", "spec_helper")
require 'mcollective'
require 'json'
include MCollective::RPC

NODE = "devnailgun.mirantis.com"

describe "MCollective" do
  context "When MC agent is up and running" do
    it "it should send echo message to MC agent and get it back" do
      data_to_send = "simple message of node '#{NODE}'"
      mc = rpcclient("fake")
      mc.progress = false
      mc.discover(:nodes => [NODE])
      stats = mc.echo(:msg => data_to_send)
      check_mcollective_result(stats)
      stats[0].results[:data][:msg].should eql("Hello, it is my reply: #{data_to_send}")
    end

    it "it should update facts file with new key-value and could get it back" do
      data_to_send = {"anykey" => rand(2**30).to_s, "other" => "static"}
      mc = rpcclient("nailyfact")
      mc.progress = false
      mc.discover(:nodes => [NODE])
      stats = mc.post(:value => data_to_send.to_json)
      check_mcollective_result(stats)

      stats = mc.get(:key => "anykey")
      check_mcollective_result(stats)
      stats[0].results[:data][:value].should eql(data_to_send['anykey'])
      stats = mc.get(:key => "other")
      check_mcollective_result(stats)
      stats[0].results[:data][:value].should eql(data_to_send['other'])
    end
  end
end

private

def check_mcollective_result(stats)
  stats.should have(1).items
  stats[0].results[:statuscode].should eql(0)
end
