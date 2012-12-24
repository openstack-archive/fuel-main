require 'json'
require 'timeout'

module Astute
  module PuppetdDeployer
    private

    def self.calc_nodes_status(last_run, prev_run)
      all_nodes = last_run.map {|n| n.results[:sender]}
      finished = last_run.select {|x| x.results[:data][:time]['last_run'] != 
          prev_run.select {|ps|
              ps.results[:sender] == x.results[:sender]
          }[0].results[:data][:time]['last_run']}

      error_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] != 0}.map {|x| {'uid' => x.results[:sender], 'status' => 'error'}}
      succeed_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] == 0}.map {|x| {'uid' => x.results[:sender], 'status' => 'ready'}}
      idle_nodes_uids = last_run.map {|n| n.results[:sender]} - finished.map {|n| n.results[:sender]}
      idle_nodes = idle_nodes_uids.map {|n| {'uid' => n, 'status' => 'idle'}}
      nodes_to_check = idle_nodes + succeed_nodes + error_nodes
      unless nodes_to_check.size == last_run.size
        raise "Internal error in nodes statuses calculation. Statuses calculated: #{nodes_to_check.inspect},"
                    "nodes passed to check statuses of: #{last_run.map {|n| n.results[:sender]}}"
      end
      return nodes_to_check
    end

    public
    def self.deploy(ctx, nodes, deployLogParser, retries=2)
      uids = nodes.map {|n| n['uid']}
      puppetd = MClient.new(ctx, "puppetd", uids)
      prev_summary = puppetd.last_run_summary

      # Keep info about retries for each node
      node_retries = {}
      uids.each {|x| node_retries.merge!({x => retries}) }

      begin
        deployLogParser.add_separator(nodes)
      rescue Exception => e
        Astute.logger.warn "Some error occured when add separator to logs: #{e.message}, trace: #{e.backtrace.inspect}"
      end

      Astute.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        # Yes, we polling here and yes, it's temporary.
        # As a better implementation we can later use separate queue to get result, ex. http://www.devco.net/archives/2012/08/19/mcollective-async-result-handling.php
        # or we can rewrite puppet agent not to fork, and increase ttl for mcollective RPC.
        puppetd.runonce
        nodes_to_check = nodes.map { |n| {'uid' => n['uid'], 'status' => nil} }
        last_run = prev_summary
        while nodes_to_check.any?
          nodes_to_check = calc_nodes_status(last_run, prev_summary)
          Astute.logger.debug "Nodes statuses: #{nodes_to_check.inspect}"
          nodes_ready = nodes_to_check.select { |n| n['status'] == 'ready' }
          nodes_error = nodes_to_check.select { |n| n['status'] == 'error' }

          # Process retries
          nodes_to_retry = []
          nodes_error.each do |n|
            uid = n['uid']
            if node_retries[uid] > 0
              node_retries[uid] -= 1
              # It's a bit hacky. Remove node from nodes_error if we will retry it.
              # This hack is required for reporting: we don't want to report error node if it will be retried.
              # Later on we will need to say the user that we are retrying.
              nodes_error.delete_if {|x| x['uid'] == uid }
              nodes_to_retry += [uid]
            end
          end
          if nodes_to_retry.any?
            Astute.logger.info "Retrying to run puppet for following error nodes: #{nodes_to_retry.join(',')}"
            puppetd.discover(:nodes => nodes_to_retry)
            puppetd.runonce
          end
          # /end of processing retries

          nodes_idle = nodes_to_check.select { |n| n['status'] == 'idle' }
          nodes_to_report = nodes_ready + nodes_error
          nodes_progress = []
          if nodes_idle.any?
            begin
              nodes_progress = deployLogParser.progress_calculate(nodes_idle)
              Astute.logger.debug "Got progress for nodes: #{nodes_progress.inspect}"
              # Nodes with progress are idle, so they are not included in nodes_to_report yet
              nodes_to_report += nodes_progress
            rescue Exception => e
              Astute.logger.warn "Some error occured when parse logs for nodes progress: #{e.message}, trace: #{e.backtrace.inspect}"
            end
          end
          ctx.reporter.report('nodes' => nodes_to_report) if nodes_to_report.any?
          # we will iterate only over idle nodes and those that we restart deployment for
          nodes_to_check = nodes_idle + nodes_to_retry.map {|n| {'uid' => n, 'status' => 'idle'} }
          break if nodes_to_check.empty?

          sleep 2
          puppetd.discover(:nodes => nodes_to_check.map {|x| x['uid']})
          last_run = puppetd.last_run_summary
        end
      end
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
