#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")
include Astute

describe "Puppetd" do
  include SpecHelpers
  context "PuppetdDeployer" do
    before :each do
      @ctx = mock
      @ctx.stubs(:task_id)
      @reporter = mock('reporter')
      @ctx.stubs(:reporter).returns(ProxyReporter.new(@reporter))
      @ctx.stubs(:deploy_log_parser).returns(Astute::LogParser::NoParsing.new)
    end

    it "reports ready status for node if puppet deploy finished successfully" do
      @reporter.expects(:report).with('nodes' => [{'uid' => '1', 'status' => 'ready', 'progress' => 100}])
      last_run_result = {:data=>
          {:time=>{"last_run"=>1358425701},
           :status => "running", :resources => {'failed' => 0},
           :running => 1, :idling => 0},
           :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000

      last_run_result_finished = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_finished[:data][:status] = 'stopped'
      last_run_result_finished[:data][:time]['last_run'] = 1358427000

      nodes = [{'uid' => '1'}]

      rpcclient = mock_rpcclient(nodes)

      rpcclient_valid_result = mock_mc_result(last_run_result)
      rpcclient_new_res = mock_mc_result(last_run_result_new)
      rpcclient_finished_res = mock_mc_result(last_run_result_finished)

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
          
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      Astute::PuppetdDeployer.deploy(@ctx, nodes, retries=0)
    end

    it "doesn't report ready status for node if change_node_status disabled" do
      @reporter.expects(:report).never
      last_run_result = {:data=>
          {:time=>{"last_run"=>1358425701},
           :status => "running", :resources => {'failed' => 0},
           :running => 1, :idling => 0},
           :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000

      last_run_result_finished = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_finished[:data][:status] = 'stopped'
      last_run_result_finished[:data][:time]['last_run'] = 1358427000

      nodes = [{'uid' => '1'}]

      rpcclient = mock_rpcclient(nodes)

      rpcclient_valid_result = mock_mc_result(last_run_result)
      rpcclient_new_res = mock_mc_result(last_run_result_new)
      rpcclient_finished_res = mock_mc_result(last_run_result_finished)

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
          
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      Astute::PuppetdDeployer.deploy(@ctx, nodes, retries=0, change_node_status=false)
    end

    it "publishes error status for node if puppet failed" do
      @reporter.expects(:report).with('nodes' => [{'status' => 'error',
        'error_type' => 'deploy', 'uid' => '1'}])

      last_run_result = {:statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"last_run"=>1358425701},
           :resources=>{"failed"=>0}, :status => "running",
           :running => 1, :idling => 0, :runtime => 100},
         :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000
      last_run_result_new[:data][:resources]['failed'] = 1

      nodes = [{'uid' => '1'}]

      last_run_result_finished = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_finished[:data][:status] = 'stopped'
      last_run_result_finished[:data][:time]['last_run'] = 1358427000
      last_run_result_finished[:data][:resources]['failed'] = 1

      rpcclient = mock_rpcclient(nodes)

      rpcclient_valid_result = mock_mc_result(last_run_result)
      rpcclient_new_res = mock_mc_result(last_run_result_new)
      rpcclient_finished_res = mock_mc_result(last_run_result_finished)

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, retries=0)
    end

    it "doesn't publish error status for node if change_node_status disabled" do
      @reporter.expects(:report).never

      last_run_result = {:statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"last_run"=>1358425701},
           :resources=>{"failed"=>0}, :status => "running",
           :running => 1, :idling => 0, :runtime => 100},
         :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000
      last_run_result_new[:data][:resources]['failed'] = 1

      nodes = [{'uid' => '1'}]

      last_run_result_finished = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_finished[:data][:status] = 'stopped'
      last_run_result_finished[:data][:time]['last_run'] = 1358427000
      last_run_result_finished[:data][:resources]['failed'] = 1

      rpcclient = mock_rpcclient(nodes)

      rpcclient_valid_result = mock_mc_result(last_run_result)
      rpcclient_new_res = mock_mc_result(last_run_result_new)
      rpcclient_finished_res = mock_mc_result(last_run_result_finished)

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, retries=0, change_node_status=false)
    end

    it "retries to run puppet if it fails" do
      @reporter.expects(:report).with('nodes' => [{'uid' => '1', 'status' => 'ready', 'progress' => 100}])

      last_run_result = {:statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"last_run"=>1358425701},
           :resources=>{"failed"=>0}, :status => "running",
           :running => 1, :idling => 0, :runtime => 100},
         :sender=>"1"}
      last_run_failed = Marshal.load(Marshal.dump(last_run_result))
      last_run_failed[:data][:time]['last_run'] = 1358426000
      last_run_failed[:data][:resources]['failed'] = 1
      last_run_failed[:data][:status] = 'stopped'

      last_run_fixing = Marshal.load(Marshal.dump(last_run_result))
      last_run_fixing[:data][:time]['last_run'] = 1358426000
      last_run_fixing[:data][:resources]['failed'] = 1
      last_run_fixing[:data][:status] = 'running'

      last_run_success = Marshal.load(Marshal.dump(last_run_result))
      last_run_success[:data][:time]['last_run'] = 1358428000
      last_run_success[:data][:status] = 'stopped'

      nodes = [{'uid' => '1'}]

      rpcclient = mock_rpcclient(nodes)

      rpcclient_valid_result = mock_mc_result(last_run_result)
      rpcclient_failed = mock_mc_result(last_run_failed)
      rpcclient_fixing = mock_mc_result(last_run_fixing)
      rpcclient_succeed = mock_mc_result(last_run_success)

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_failed]).then.
          returns([rpcclient_failed]).then.
          returns([rpcclient_fixing]).then.
          returns([rpcclient_succeed])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, retries=1)
    end
  end
end
