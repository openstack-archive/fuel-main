require 'json'
require 'timeout'

module Astute
  module PuppetdDeployer
    private
    # Runs puppetd.runonce only if puppet is not running on the host at the time
    # If it does running, it waits a bit and tries again.
    # Returns list of nodes uids which appear to be with hung puppet.
    def self.puppetd_runonce(puppetd, uids)
      started = Time.now.to_i
      while Time.now.to_i - started < Astute.config.PUPPET_FADE_TIMEOUT
        puppetd.discover(:nodes => uids)
        last_run = puppetd.last_run_summary
        running = last_run.select {|x| x.results[:data][:status] == 'running'}.map {|n| n.results[:sender]}
        not_running = uids - running
        if not_running.any?
          puppetd.discover(:nodes => not_running)
          puppetd.runonce
        end
        uids = running
        break if uids.empty?
        sleep Astute.config.PUPPET_FADE_INTERVAL
      end
      Astute.logger.debug "puppetd_runonce completed within #{Time.now.to_i - started} seconds."
      Astute.logger.debug "Following nodes have puppet hung: '#{running.join(',')}'" if running.any?
      running
    end

    def self.calc_nodes_status(last_run, prev_run)
      # Finished are those which are not in running state,
      #   and changed their last_run time, which is changed after application of catalog,
      #   at the time of updating last_run_summary file. At that particular time puppet is
      #   still running, and will finish in a couple of seconds.
      finished = last_run.select {|x| x.results[:data][:time]['last_run'] != 
          prev_run.select {|ps|
              ps.results[:sender] == x.results[:sender]
          }[0].results[:data][:time]['last_run'] and x.results[:data][:status] != 'running'}

      # Looking for error_nodes among only finished - we don't bother previous failures
      error_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] != 0}.map {|x| x.results[:sender]}

      succeed_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] == 0}.map {|x| x.results[:sender]}

      # Running are all which didn't appear in finished
      running_nodes = last_run.map {|n| n.results[:sender]} - finished.map {|n| n.results[:sender]}

      nodes_to_check = running_nodes + succeed_nodes + error_nodes
      unless nodes_to_check.size == last_run.size
        raise "Shoud never happen. Internal error in nodes statuses calculation. Statuses calculated for: #{nodes_to_check.inspect},"
                    "nodes passed to check statuses of: #{last_run.map {|n| n.results[:sender]}}"
      end
      {'succeed' => succeed_nodes, 'error' => error_nodes, 'running' => running_nodes}
    end

    public
    def self.deploy(ctx, nodes, retries=2, change_node_status=true)
      # TODO: can we hide retries, ignore_failure into @ctx ?
      uids = nodes.map {|n| n['uid']}
      # TODO(mihgen): handle exceptions from mclient, raised if agent does not respond or responded with error
      puppetd = MClient.new(ctx, "puppetd", uids)
      prev_summary = puppetd.last_run_summary

      # Keep info about retries for each node
      node_retries = {}
      uids.each {|x| node_retries.merge!({x => retries}) }

      Astute.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{Astute.config.PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(Astute.config.PUPPET_TIMEOUT) do
        puppetd_runonce(puppetd, uids)
        nodes_to_check = uids
        last_run = prev_summary
        while nodes_to_check.any?
          calc_nodes = calc_nodes_status(last_run, prev_summary)
          Astute.logger.debug "Nodes statuses: #{calc_nodes.inspect}"

          # At least we will report about successfully deployed nodes
          nodes_to_report = []
          nodes_to_report.concat(calc_nodes['succeed'].map { |n| {'uid' => n, 'status' => 'ready'} }) if change_node_status

          # Process retries
          nodes_to_retry = []
          calc_nodes['error'].each do |uid|
            if node_retries[uid] > 0
              node_retries[uid] -= 1
              Astute.logger.debug "Puppet on node #{uid.inspect} will be restarted. "\
                                  "#{node_retries[uid]} retries remained."
              nodes_to_retry << uid
            else
              Astute.logger.debug "Node #{uid.inspect} has failed to deploy. There is no more retries for puppet run."
              nodes_to_report << {'uid' => uid, 'status' => 'error', 'error_type' => 'deploy'} if change_node_status
            end
          end
          if nodes_to_retry.any?
            Astute.logger.info "Retrying to run puppet for following error nodes: #{nodes_to_retry.join(',')}"
            puppetd_runonce(puppetd, nodes_to_retry)
            # We need this magic with prev_summary to reflect new puppetd run statuses..
            prev_summary.delete_if { |x| nodes_to_retry.include?(x.results[:sender]) }
            prev_summary += last_run.select { |x| nodes_to_retry.include?(x.results[:sender]) }
          end
          # /end of processing retries

          if calc_nodes['running'].any?
            begin
              # Pass nodes because logs calculation needs IP address of node, not just uid
              nodes_progress = ctx.deploy_log_parser.progress_calculate(calc_nodes['running'], nodes)
              if nodes_progress.any?
                Astute.logger.debug "Got progress for nodes: #{nodes_progress.inspect}"
                # Nodes with progress are running, so they are not included in nodes_to_report yet
                nodes_progress.map! {|x| x.merge!({'status' => 'deploying'})}
                nodes_to_report += nodes_progress
              end
            rescue Exception => e
              Astute.logger.warn "Some error occurred when parse logs for nodes progress: #{e.message}, "\
                                 "trace: #{e.backtrace.inspect}"
            end
          end
          ctx.reporter.report('nodes' => nodes_to_report) if nodes_to_report.any?

          # we will iterate only over running nodes and those that we restart deployment for
          nodes_to_check = calc_nodes['running'] + nodes_to_retry
          break if nodes_to_check.empty?

          sleep Astute.config.PUPPET_DEPLOY_INTERVAL
          puppetd.discover(:nodes => nodes_to_check)
          last_run = puppetd.last_run_summary
        end
      end
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run "\
                         "for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
