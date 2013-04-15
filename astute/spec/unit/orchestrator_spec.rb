#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe Astute::Orchestrator do
  include SpecHelpers
  before(:each) do
    @orchestrator = Astute::Orchestrator.new
    @reporter = mock('reporter')
    @reporter.stub_everything
  end

  it "must be able to return node type" do
    nodes = [{'uid' => '1'}]
    res = {:data => {:node_type => 'target'},
           :sender=>"1"}

    mc_res = mock_mc_result(res)
    mc_timeout = 5

    rpcclient = mock_rpcclient(nodes, mc_timeout)
    rpcclient.expects(:get_type).once.returns([mc_res])

    types = @orchestrator.node_type(@reporter, 'task_uuid', nodes, mc_timeout)
    types.should eql([{"node_type"=>"target", "uid"=>"1"}])
  end

  it "must be able to complete verify_networks" do
    nodes = [
      {
        'uid' => '1',
        'networks' => [
          {
            'iface' => 'eth0',
            'vlans' => [100, 101]
          }
        ]
      },
      {
        'uid' => '2',
        'networks' => [
          {
            'iface' => 'eth0',
            'vlans' => [100, 101]
          }
        ]
      },
    ]
    res1 = {:data => {:uid=>"1",
                      :neighbours => {"eth0" => {"100" => {"1" => ["eth0"], "2" => ["eth0"]},
                                                 "101" => {"1" => ["eth0"]}
                                                }
                                     }
                     },
            :sender=>"1"
           }
    res2 = {:data => {:uid=>"2",
                      :neighbours => {"eth0" => {"100" => {"1" => ["eth0"], "2" => ["eth0"]},
                                                 "101" => {"1" => ["eth0"], "2" => ["eth0"]}
                                                }
                                     }
                     },
            :sender=>"2"
           }
    valid_res = {:statuscode => 0, :sender => '1'}
    mc_res1 = mock_mc_result(res1)
    mc_res2 = mock_mc_result(res2)
    mc_valid_res = mock_mc_result

    rpcclient = mock_rpcclient(nodes)

    rpcclient.expects(:get_probing_info).once.returns([mc_res1, mc_res2])
    nodes.each do |n|

      rpcclient.expects(:discover).with(:nodes => [n['uid'].to_s]).at_least_once

      data_to_send = {}
      n['networks'].each{|net| data_to_send[net['iface']] = net['vlans'].join(",") }
      rpcclient.expects(:start_frame_listeners).with(:interfaces => data_to_send.to_json).returns([mc_valid_res]*2)
      rpcclient.expects(:send_probing_frames).with(:interfaces => data_to_send.to_json).returns([mc_valid_res]*2)

    end
    Astute::MClient.any_instance.stubs(:rpcclient).returns(rpcclient)

    res = @orchestrator.verify_networks(@reporter, 'task_uuid', nodes)
    expected = {"nodes" => [{"networks" => [{"iface"=>"eth0", "vlans"=>[100]}], "uid"=>"1"},
                            {"networks"=>[{"iface"=>"eth0", "vlans"=>[100, 101]}], "uid"=>"2"}]}
    res.should eql(expected)
  end

  it "verify_network returns error if nodes list is empty" do
    res = @orchestrator.verify_networks(@reporter, 'task_uuid', [])
    res.should eql({'status' => 'error', 'error' => "Nodes list is empty. Nothing to check."})
  end

  it "verify_network returns all vlans passed if only one node provided" do
    nodes = [
      {
        'uid' => '1',
        'networks' => [
          {
            'iface' => 'eth0',
            'vlans' => [100, 101]
          }
        ]
      }
    ]
    res = @orchestrator.verify_networks(@reporter, 'task_uuid', nodes)
    expected = {"nodes" => [{"networks" => [{"iface"=>"eth0", "vlans"=>[100, 101]}], "uid"=>"1"}]}
    res.should eql(expected)
  end

  it "in remove_nodes, it returns empty list if nodes are not provided" do
    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', [])
    res.should eql({'nodes' => []})
  end

  it "remove_nodes cleans nodes and reboots them" do
    removed_hash = {:sender => '1',
                    :data => {:rebooted => true}}
    error_hash = {:sender => '2',
                  :data => {:rebooted => false, :error_msg => 'Could not reboot'}}
    nodes = [{'uid' => 1}, {'uid' => 2}]

    rpcclient = mock_rpcclient
    mc_removed_res = mock_mc_result(removed_hash)
    mc_error_res = mock_mc_result(error_hash)

    rpcclient.expects(:erase_node).at_least_once.with(:reboot => true).returns([mc_removed_res, mc_error_res])

    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', nodes)
    res.should eql({'nodes' => [{'uid' => '1'}], 'status' => 'error',
                    'error_nodes' => [{"uid"=>"2", "error"=>"RPC method 'erase_node' failed "\
                                                            "with message: Could not reboot"}]})
  end

  it "it calls deploy method with valid arguments" do
    nodes = [{'uid' => 1}]
    attrs = {'a' => 'b'}
    Astute::DeploymentEngine::NailyFact.any_instance.expects(:deploy).
                                                     with([{'uid' => '1'}], attrs)
    @orchestrator.deploy(@reporter, 'task_uuid', nodes, attrs)
  end

  it "deploy method raises error if nodes list is empty" do
    expect {@orchestrator.deploy(@reporter, 'task_uuid', [], {})}.
                          to raise_error(/Nodes to deploy are not provided!/)
  end

  it "remove_nodes try to call MCAgent multiple times on error" do
    removed_hash = {:sender => '1',
                    :data => {:rebooted => true}}
    error_hash = {:sender => '2',
                  :data => {:rebooted => false, :error_msg => 'Could not reboot'}}
    nodes = [{'uid' => 1}, {'uid' => 2}]

    rpcclient = mock_rpcclient(nodes)
    mc_removed_res = mock_mc_result(removed_hash)
    mc_error_res = mock_mc_result(error_hash)

    retries = Astute.config[:MC_RETRIES]
    retries.should == 5
    rpcclient.expects(:discover).with(:nodes => ['2']).times(retries)
    rpcclient.expects(:erase_node).times(retries + 1).with(:reboot => true).returns([mc_removed_res, mc_error_res]).then.returns([mc_error_res])

    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', nodes)
    res.should eql({'nodes' => [{'uid' => '1'}], 'status' => 'error',
                    'error_nodes' => [{"uid"=>"2", "error"=>"RPC method 'erase_node' failed "\
                                                            "with message: Could not reboot"}]})
  end

  it "remove_nodes try to call MCAgent multiple times on no response" do
    removed_hash = {:sender => '2', :data => {:rebooted => true}}
    then_removed_hash = {:sender => '3', :data => {:rebooted => true}}
    nodes = [{'uid' => 1}, {'uid' => 2}, {'uid' => 3}]

    rpcclient = mock_rpcclient(nodes)
    mc_removed_res = mock_mc_result(removed_hash)
    mc_then_removed_res = mock_mc_result(then_removed_hash)

    retries = Astute.config[:MC_RETRIES]
    rpcclient.expects(:discover).with(:nodes => %w(1 3)).times(1)
    rpcclient.expects(:discover).with(:nodes => %w(1)).times(retries - 1)
    rpcclient.expects(:erase_node).times(retries + 1).with(:reboot => true).
        returns([mc_removed_res]).then.returns([mc_then_removed_res]).then.returns([])

    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', nodes)
    res['nodes'] = res['nodes'].sort_by{|n| n['uid'] }
    res.should eql({'nodes' => [{'uid' => '2'}, {'uid' => '3'}], 'status' => 'error',
                    'error_nodes' => [{'uid'=>'1', 'error'=>'Node not answered by RPC.'}]})
  end

  it "remove_nodes and returns early if retries were successful" do
    removed_hash = {:sender => '1', :data => {:rebooted => true}}
    then_removed_hash = {:sender => '2', :data => {:rebooted => true}}
    nodes = [{'uid' => 1}, {'uid' => 2}]

    rpcclient = mock_rpcclient(nodes)
    mc_removed_res = mock_mc_result(removed_hash)
    mc_then_removed_res = mock_mc_result(then_removed_hash)

    retries = Astute.config[:MC_RETRIES]
    retries.should_not == 2
    rpcclient.expects(:discover).with(:nodes => %w(2)).times(1)
    rpcclient.expects(:erase_node).times(2).with(:reboot => true).
        returns([mc_removed_res]).then.returns([mc_then_removed_res])

    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', nodes)
    res['nodes'] = res['nodes'].sort_by{|n| n['uid'] }
    res.should eql({'nodes' => [{'uid' => '1'}, {'uid' => '2'}]})
  end

  it "remove_nodes do not fail if any of nodes failed"
end

