#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe "Orchestrator" do
  context "When initialized with defaults" do
    before(:each) do
      @orchestrator = Astute::Orchestrator.new
      @reporter = mock('reporter')
      @reporter.stub_everything
    end

    it "it must be able to return node type" do
      mc_res = {:statuscode => 0,
                :data => {:node_type => 'target'},
                :sender=>"1"}

      mc_timeout = 5

      rpcclient = mock('rpcclient') do
        stubs(:progress=)
        expects(:timeout=).with(mc_timeout)
        expects(:discover).with(:nodes => ['1']).at_least_once
      end
      rpcclient_valid_result = mock('rpcclient_valid_result') do
        stubs(:results).returns(mc_res)
        stubs(:agent).returns('node_type')
      end
      rpcclient.expects(:get_type).once.returns([rpcclient_valid_result])
      Astute::MClient.any_instance.stubs(:rpcclient).returns(rpcclient)

      types = @orchestrator.node_type(@reporter, 'task_uuid', [{'uid' => 1}], timeout=mc_timeout)
      types.should eql([{"node_type"=>"target", "uid"=>"1"}])
    end

    it "it must be able to complete verify_networks" do
      nodes = [{'uid' => '1'}, {'uid' => '2'}]
      networks = [{'id' => 1, 'vlan_id' => 100, 'cidr' => '10.0.0.0/24'},
                  {'id' => 2, 'vlan_id' => 101, 'cidr' => '192.168.0.0/24'}]
      mc_res1 = {:statuscode => 0,
                 :data => {:uid=>"1", 
                           :neighbours => {"eth0" => {"100" => {"1" => ["eth0"], "2" => ["eth0"]},
                                                      "101" => {"1" => ["eth0"]}
                                                     }
                                          }
                          },
                 :sender=>"1"
                }
      mc_res2 = {:statuscode => 0,
                 :data => {:uid=>"2", 
                           :neighbours => {"eth0" => {"100" => {"1" => ["eth0"], "2" => ["eth0"]},
                                                      "101" => {"1" => ["eth0"], "2" => ["eth0"]}
                                                     }
                                          }
                          },
                 :sender=>"2"
                }
      just_valid_res = {:statuscode => 0, :sender => '1'}

      rpcclient = mock('rpcclient') do
        stubs(:progress=)
        expects(:discover).with(:nodes => nodes.map {|x| x['uid']}).at_least_once
      end
      valid_res = mock('valid_res') do
        stubs(:results).returns(just_valid_res)
        stubs(:agent).returns('net_probe')
      end
      net_info_res1 = mock('net_info_res') do
        stubs(:results).returns(mc_res1)
        stubs(:agent).returns('net_probe')
      end
      net_info_res2 = mock('net_info_res') do
        stubs(:results).returns(mc_res2)
        stubs(:agent).returns('net_probe')
      end
      rpcclient.expects(:start_frame_listeners).once.returns([valid_res]*2)
      rpcclient.expects(:send_probing_frames).once.returns([valid_res]*2)
      rpcclient.expects(:get_probing_info).once.returns([net_info_res1, net_info_res2])
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
  end
end

