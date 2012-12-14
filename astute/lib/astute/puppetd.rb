require 'json'
require 'timeout'

module Astute
  module PuppetdDeployer
    private
    def self.calc_error_nodes(last_run_summary)
      error_nodes = last_run_summary.select { |n|
            n.results[:data][:resources]['failed'] != 0}.map {|x| x.results[:sender]}
      return error_nodes
    end

    def self.wait_until_puppet_done(ctx, puppetd, prev_summary)
      prev_error_nodes = calc_error_nodes(prev_summary)
      last_run = prev_summary
      while last_run.all? {|x| x.results[:data][:time]['last_run'] ==
            prev_summary.select {|ps|
                ps.results[:sender] == x.results[:sender]
            }[0].results[:data][:time]['last_run']}
        sleep 2
        # last_run variable is used in while and to calculate error nodes (the line below)
        last_run = puppetd.last_run_summary
        error_nodes = calc_error_nodes(last_run)
        new_error_nodes = error_nodes.select { |n| not prev_error_nodes.include?(n) }
        if new_error_nodes.any?
          nodes_to_report = new_error_nodes.map { |node| {'uid' => node, 'status' => 'error'} }
          ctx.reporter.report({'nodes' => nodes_to_report})
          # We want to send error message only once (only when status is changed)
          prev_error_nodes = new_error_nodes
        end
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
        wait_until_puppet_done(ctx, puppetd, lastrun_summary)
      end
      summary = puppetd.last_run_summary.map { |x| {x.results[:sender] => x.results[:data][:resources]} }
      Astute.logger.debug "Results of puppet run from all nodes: #{summary.inspect}"
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
