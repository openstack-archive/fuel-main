#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")
include Astute

describe "Puppetd" do
  context "PuppetdDeployer" do
    it "reports ready status for node if puppet deploy finished successfully" do
      @ctx = mock
      @ctx.stubs(:task_id)
      reporter = mock('reporter')
      @ctx.stubs(:reporter).returns(reporter)

      reporter.expects(:report).with('nodes' => [{'uid' => '1', 'status' => 'ready'}])

      last_run_result = {:statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"last_run"=>1358425701},
           :resources=>{"failed"=>0}, :status => "running",
           :running => 1, :idling => 0, :runtime => 100},
         :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000

      last_run_result_finished = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_finished[:data][:status] = 'stopped'
      last_run_result_finished[:data][:time]['last_run'] = 1358427000

      nodes = [{'uid' => '1'}]

      deploy_log_parser = mock('deploy_log_parser')
      rpcclient = mock('rpcclient') do
        stubs(:progress=)
        nodes_to_discover = nodes.map { |n| n['uid'] }
        expects(:discover).with(:nodes => nodes_to_discover).at_least_once
      end

      rpcclient_valid_result = mock('rpcclient_valid_result') do
        stubs(:results).returns(last_run_result)
        stubs(:agent).returns('faketest')
      end

      rpcclient_new_res = mock('rpcclient_new_res') do
        stubs(:results).returns(last_run_result_new)
        stubs(:agent).returns('faketest')
      end

      rpcclient_finished_res = mock('rpcclient_finished_res') do
        stubs(:results).returns(last_run_result_finished)
        stubs(:agent).returns('faketest')
      end

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
          
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, deploy_log_parser, retries=0)
    end

    it "publishes error status for node if puppet failed" do
      @ctx = mock
      @ctx.stubs(:task_id)
      reporter = mock('reporter')
      @ctx.stubs(:reporter).returns(reporter)

      reporter.expects(:report).with('nodes' => [{'status' => 'error', 'error_type' => 'deploy', 'uid' => '1'}])

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

      deploy_log_parser = mock('deploy_log_parser')
      rpcclient = mock('rpcclient') do
        stubs(:progress=)
        nodes_to_discover = nodes.map { |n| n['uid'] }
        expects(:discover).with(:nodes => nodes_to_discover).at_least_once
      end

      rpcclient_valid_result = mock('rpcclient_valid_result') do
        stubs(:results).returns(last_run_result)
        stubs(:agent).returns('faketest')
      end

      rpcclient_new_res = mock('rpcclient_new_res') do
        stubs(:results).returns(last_run_result_new)
        stubs(:agent).returns('faketest')
      end

      rpcclient_finished_res = mock('rpcclient_finished_res') do
        stubs(:results).returns(last_run_result_finished)
        stubs(:agent).returns('faketest')
      end

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_new_res]).then.
          returns([rpcclient_finished_res])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, deploy_log_parser, retries=0)
    end

    it "retries to run puppet if it fails" do
      @ctx = mock
      @ctx.stubs(:task_id)
      reporter = mock('reporter')
      @ctx.stubs(:reporter).returns(reporter)

      reporter.expects(:report).with('nodes' => [{'uid' => '1', 'status' => 'ready'}])

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

      deploy_log_parser = mock('deploy_log_parser')
      rpcclient = mock('rpcclient') do
        stubs(:progress=)
        nodes_to_discover = nodes.map { |n| n['uid'] }
        expects(:discover).with(:nodes => nodes_to_discover).at_least_once
      end

      rpcclient_valid_result = mock('rpcclient_valid_result') do
        stubs(:results).returns(last_run_result)
        stubs(:agent).returns('faketest')
      end

      rpcclient_failed = mock('rpcclient_failed') do
        stubs(:results).returns(last_run_failed)
        stubs(:agent).returns('faketest')
      end

      rpcclient_fixing = mock('rpcclient_fixing') do
        stubs(:results).returns(last_run_fixing)
        stubs(:agent).returns('faketest')
      end

      rpcclient_succeed = mock('rpcclient_succeed') do
        stubs(:results).returns(last_run_success)
        stubs(:agent).returns('faketest')
      end

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_valid_result]).then.
          returns([rpcclient_failed]).then.
          returns([rpcclient_failed]).then.
          returns([rpcclient_fixing]).then.
          returns([rpcclient_succeed])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, deploy_log_parser, retries=1)
    end
  end
end
