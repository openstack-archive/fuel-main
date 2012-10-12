require 'json'
require 'timeout'
require 'mcollective'

PUPPET_TIMEOUT = 30*60

module Orchestrator
  class PuppetDeployer
    include MCollective::RPC
    include ::Orchestrator

    private

    def wait_until_puppet_done(mc, previous_runs, task_id="")
      # Wait for first node is done, than check the next one
      # Load to mcollective is reduced by checking only one machine at time in a set
      # In fact we need to know if whole set of machines finished deployment
      previous_runs.each do |res|
        prev_run = res['ts']
        last_run = prev_run
        while last_run == prev_run
          mc.discover(:nodes => [res['sender']])
          puppet_status = mc.status
          # logging to false, otherwise we get a message every second
          self.check_mcollective_result(puppet_status, task_id, log=false)
          last_run = puppet_status[0].results[:data][:lastrun]
          sleep 1 if last_run == prev_run
        end
      end
    end

    public
    def deploy(reporter, task_id, nodes)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      mc = rpcclient("puppetd")
      mc.progress = false
      mc.discover(:nodes => macs)
      puppet_status = mc.status
      self.check_mcollective_result(puppet_status, task_id)

      # In results :lastrun we get the time when Puppet finished it's work last time
      previous_runs = puppet_status.map { |res| {'sender' => res.results[:sender],
                                                 'ts' => res.results[:data][:lastrun]} }

      self.check_mcollective_result(mc.runonce, task_id)

      reporter.report({'progress' => 2})

      ::Orchestrator.logger.debug "Waiting for puppet to finish deploymen on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        # Yes, we polling here and yes, it's temporary.
        # As a better implementation we can later use separate queue to get result, ex. http://www.devco.net/archives/2012/08/19/mcollective-async-result-handling.php
        # or we can rewrite puppet agent not to fork, and increase ttl for mcollective RPC.
        wait_until_puppet_done(mc, previous_runs, task_id)
      end
      time_spent = Time.now - time_before
      ::Orchestrator.logger.info "Spent #{time_spent} seconds on puppet run for following nodes(macs): #{nodes.map {|n| n['mac']}.join(',')}"

      reporter.report({'progress' => 100})
    end
  end
end
  
