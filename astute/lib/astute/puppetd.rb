require 'json'
require 'timeout'

module Astute
  module PuppetdDeployer
    private

    def self.wait_until_puppet_done(ctx, puppetd, prev_summary)
      last_run = prev_summary
      while last_run.all? {|x| x.results[:data][:time]['last_run'] ==
            prev_summary.select {|ps|
                ps.results[:sender] == x.results[:sender]
            }[0].results[:data][:time]['last_run']}
        sleep 2
        last_run = puppetd.last_run_summary
        error_nodes = last_run.map {|x| {'uid' => x.results[:sender],
                                         'status' =>
                x.results[:data][:resources]['failed'] != 0 ? 'error' : 'idle'} }.select { |n|
                    n['status'] == 'error' }

        ctx.reporter.report({'nodes' => error_nodes}) if error_nodes.any?
      end
      last_run
    end

    public
    def self.deploy(ctx, nodes)
      uids = nodes.map {|n| n['uid']}
      puppetd = MClient.new(ctx, "puppetd", uids)
      lastrun_summary = puppetd.last_run_summary

      puppetd.runonce

      Astute.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        # Yes, we polling here and yes, it's temporary.
        # As a better implementation we can later use separate queue to get result, ex. http://www.devco.net/archives/2012/08/19/mcollective-async-result-handling.php
        # or we can rewrite puppet agent not to fork, and increase ttl for mcollective RPC.
        latest_run_summary = wait_until_puppet_done(ctx, puppetd, lastrun_summary)
      end
      summary = latest_run_summary.map { |x| {x.results[:sender] => x.results[:data][:resources]} }
      Astute.logger.debug "Results of puppet run from all nodes: #{summary.inspect}"
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
