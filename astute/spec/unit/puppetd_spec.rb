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

      last_run_result = {:statusmsg=>"OK", :statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"filebucket"=>0.000971, "last_run"=>1358425701,
              "file"=>0.000593, "exec"=>3.555788, "config_retrieval"=>0.0796780586242676,
              "total"=>3.63703005862427}, :events=>{"success"=>1, "failure"=>0, "total"=>1},
              :version=>{"puppet"=>"3.0.2", "config"=>1356783505},
              :resources=>{"restarted"=>0, "failed"=>0, "changed"=>1, "skipped"=>6,
                  "total"=>9, "out_of_sync"=>1, "scheduled"=>0, "failed_to_restart"=>0}},
          :status => "running",
          :running => 1,
          :enabled => 1,
          :idling => 0,
          :stopped => 0,
          :lastrun => 1358425701,
          :runtime => 100,
          :output => "Currently running; last completed run 100 seconds ago",
          :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000
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

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.returns([rpcclient_new_res])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, deploy_log_parser)
    end

    it "publishes error status for node if puppet failed" do
      @ctx = mock
      @ctx.stubs(:task_id)
      reporter = mock('reporter')
      @ctx.stubs(:reporter).returns(reporter)

      reporter.expects(:report).with('nodes' => [{'status' => 'error', 'error_type' => 'deploy', 'uid' => '1'}])

      last_run_result = {:statusmsg=>"OK", :statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"filebucket"=>0.000971, "last_run"=>1358425701,
              "file"=>0.000593, "exec"=>3.555788, "config_retrieval"=>0.0796780586242676,
              "total"=>3.63703005862427}, :events=>{"success"=>1, "failure"=>0, "total"=>1},
              :version=>{"puppet"=>"3.0.2", "config"=>1356783505},
              :resources=>{"restarted"=>0, "failed"=>0, "changed"=>1, "skipped"=>6,
                  "total"=>9, "out_of_sync"=>1, "scheduled"=>0, "failed_to_restart"=>0}},
          :status => "running",
          :running => 1,
          :enabled => 1,
          :idling => 0,
          :stopped => 0,
          :lastrun => 1358425701,
          :runtime => 100,
          :output => "Currently running; last completed run 100 seconds ago",
          :sender=>"1"}
      last_run_result_new = Marshal.load(Marshal.dump(last_run_result))
      last_run_result_new[:data][:time]['last_run'] = 1358426000
      last_run_result_new[:data][:resources]['failed'] = 1
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

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.returns([rpcclient_new_res])
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

      last_run_result = {:statusmsg=>"OK", :statuscode=>0, :data=>
          {:changes=>{"total"=>1}, :time=>{"filebucket"=>0.000971, "last_run"=>1358425701,
              "file"=>0.000593, "exec"=>3.555788, "config_retrieval"=>0.0796780586242676,
              "total"=>3.63703005862427}, :events=>{"success"=>1, "failure"=>0, "total"=>1},
              :version=>{"puppet"=>"3.0.2", "config"=>1356783505},
              :resources=>{"restarted"=>0, "failed"=>0, "changed"=>1, "skipped"=>6,
                  "total"=>9, "out_of_sync"=>1, "scheduled"=>0, "failed_to_restart"=>0}},
          :status => "running",
          :running => 1,
          :enabled => 1,
          :idling => 0,
          :stopped => 0,
          :lastrun => 1358425701,
          :runtime => 100,
          :output => "Currently running; last completed run 100 seconds ago",
          :sender=>"1"}
      last_run_failed = Marshal.load(Marshal.dump(last_run_result))
      last_run_failed[:data][:time]['last_run'] = 1358426000
      last_run_failed[:data][:resources]['failed'] = 1

      last_run_success = Marshal.load(Marshal.dump(last_run_result))
      last_run_success[:data][:time]['last_run'] = 1358427000

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

      rpcclient_succeed = mock('rpcclient_succeed') do
        stubs(:results).returns(last_run_success)
        stubs(:agent).returns('faketest')
      end

      rpcclient.stubs(:last_run_summary).returns([rpcclient_valid_result]).then.
          returns([rpcclient_failed]).then.returns([rpcclient_succeed])
      rpcclient.expects(:runonce).at_least_once.returns([rpcclient_valid_result])

      MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
      Astute::PuppetdDeployer.deploy(@ctx, nodes, deploy_log_parser, retries=1)
    end
  end
end
