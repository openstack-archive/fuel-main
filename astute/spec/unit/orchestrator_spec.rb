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
    nodes = [{'uid' => '1'}, {'uid' => '2'}]
    networks = [{'id' => 1, 'vlan_id' => 100, 'cidr' => '10.0.0.0/24'},
                {'id' => 2, 'vlan_id' => 101, 'cidr' => '192.168.0.0/24'}]
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

    rpcclient.expects(:start_frame_listeners).once.returns([mc_valid_res]*2)
    rpcclient.expects(:send_probing_frames).once.returns([mc_valid_res]*2)
    rpcclient.expects(:get_probing_info).once.returns([mc_res1, mc_res2])
    Astute::MClient.any_instance.stubs(:rpcclient).returns(rpcclient)

    res = @orchestrator.verify_networks(@reporter, 'task_uuid', nodes, networks)
    expected = {"nodes" => [{"networks" => [{"iface"=>"eth0", "vlans"=>[100]}], "uid"=>"1"},
                            {"networks"=>[{"iface"=>"eth0", "vlans"=>[100, 101]}], "uid"=>"2"}]}
    res.should eql(expected)
  end

  it "verify_network returns error if nodes list is empty" do
    res = @orchestrator.verify_networks(@reporter, 'task_uuid', [], [])
    res.should eql({'status' => 'error', 'error' => "Nodes list is empty. Nothing to check."})
  end

  it "verify_network returns all vlans passed if only one node provided" do
    nodes = [{'uid' => '1'}]
    networks = [{'id' => 1, 'vlan_id' => 100, 'cidr' => '10.0.0.0/24'},
                {'id' => 2, 'vlan_id' => 101, 'cidr' => '192.168.0.0/24'}]
    res = @orchestrator.verify_networks(@reporter, 'task_uuid', nodes, networks)
    expected = {"nodes" => [{"networks" => [{"iface"=>"eth0", "vlans"=>[100,101]}], "uid"=>"1"}]}
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

    rpcclient = mock_rpcclient(nodes)
    mc_removed_res = mock_mc_result(removed_hash)
    mc_error_res = mock_mc_result(error_hash)

    rpcclient.expects(:erase_node).once.with(:reboot => true).returns([mc_removed_res, mc_error_res])

    res = @orchestrator.remove_nodes(@reporter, 'task_uuid', nodes)
    res.should eql({'nodes' => [{'uid' => '1'}], 'status' => 'error',
                    'error_nodes' => [{"uid"=>"2", "error"=>"RPC method 'erase_node' failed "\
                                                            "with message: Could not reboot"}]})
  end

  it "remove_nodes try to call MCAgent multiple times"
  it "remove_nodes do not fail if any of nodes failed"
end

