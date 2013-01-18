require 'json'
require 'timeout'

module Astute
  module PuppetdDeployer
    private

    def self.calc_nodes_status(last_run, prev_run)
      finished = last_run.select {|x| x.results[:data][:time]['last_run'] != 
          prev_run.select {|ps|
              ps.results[:sender] == x.results[:sender]
          }[0].results[:data][:time]['last_run']}

      failed_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] != 0}

      error_nodes = []
      idle_nodes = []
      hang_nodes = []
      now = Time.now.to_i
      failed_nodes.each do |n|
        if n.results[:data][:status] == 'running'
          if n.results[:data][:runtime] > PUPPET_FADE_TIMEOUT
            hang_nodes << n.results[:sender]
          else
            idle_nodes << n.results[:sender]
          end
        else
          error_nodes << n.results[:sender]
        end
      end

      succeed_nodes = finished.select { |n|
            n.results[:data][:resources]['failed'] == 0}.map {|x| x.results[:sender]}

      idle_nodes = last_run.map {|n| n.results[:sender]} - finished.map {|n| n.results[:sender]}

      nodes_to_check = idle_nodes + succeed_nodes + error_nodes + hang_nodes
      unless nodes_to_check.size == last_run.size
        raise "Shoud never happen. Internal error in nodes statuses calculation. Statuses calculated for: #{nodes_to_check.inspect},"
                    "nodes passed to check statuses of: #{last_run.map {|n| n.results[:sender]}}"
      end
      return {'succeed' => succeed_nodes, 'error' => error_nodes, 'idle' => idle_nodes,
              'hang' => hang_nodes}
    end

    public
    def self.deploy(ctx, nodes, deploy_log_parser, retries=2)
      uids = nodes.map {|n| n['uid']}
      puppetd = MClient.new(ctx, "puppetd", uids)
      prev_summary = puppetd.last_run_summary

      # Keep info about retries for each node
      node_retries = {}
      uids.each {|x| node_retries.merge!({x => retries}) }

      begin
        deploy_log_parser.add_separator(nodes)
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
        nodes_to_check = uids
        last_run = prev_summary
        while nodes_to_check.any?
          calc_nodes = calc_nodes_status(last_run, prev_summary)
          Astute.logger.debug "Nodes statuses: #{calc_nodes.inspect}"

          # At least we will report about successfully deployed nodes
          nodes_to_report = calc_nodes['succeed'].map { |n| {'uid' => n, 'status' => 'ready'} }
          # ... and about nodes which hung out
          if calc_nodes['hang'].any?
            Astute.logger.error "Puppet failed and couldn't stop itself on nodes #{calc_nodes['hang'].join(',')}"
            nodes_to_report += calc_nodes['hang'].map { |n| {'uid' => n, 'status' => 'error', 'error_type' => 'deploy'} }
          end

          # Process retries
          nodes_to_retry = []
          calc_nodes['error'].each do |uid|
            if node_retries[uid] > 0
              node_retries[uid] -= 1
              Astute.logger.debug "Puppet on node #{uid.inspect} will be restarted. #{node_retries[uid]} retries remained."
              nodes_to_retry << uid
            else
              Astute.logger.debug "Node #{uid.inspect}. There is no more retries for puppet run."
              nodes_to_report << {'uid' => uid, 'status' => 'error', 'error_type' => 'deploy'}
            end
          end
          if nodes_to_retry.any?
            Astute.logger.info "Retrying to run puppet for following error nodes: #{nodes_to_retry.join(',')}"
            puppetd.discover(:nodes => nodes_to_retry)
            puppetd.runonce
          end
          # /end of processing retries

          if calc_nodes['idle'].any?
            begin
              # Pass nodes because logs calculation needs IP address of node, not just uid
              nodes_progress = deploy_log_parser.progress_calculate(calc_nodes['idle'], nodes)
              Astute.logger.debug "Got progress for nodes: #{nodes_progress.inspect}"
              # Nodes with progress are idle, so they are not included in nodes_to_report yet
              nodes_to_report += nodes_progress
            rescue Exception => e
              Astute.logger.warn "Some error occured when parse logs for nodes progress: #{e.message}, trace: #{e.backtrace.inspect}"
            end
          end
          ctx.reporter.report('nodes' => nodes_to_report) if nodes_to_report.any?
          # we will iterate only over idle nodes and those that we restart deployment for
          nodes_to_check = calc_nodes['idle'] + nodes_to_retry
          break if nodes_to_check.empty?

          sleep 2
          puppetd.discover(:nodes => nodes_to_check)
          last_run = puppetd.last_run_summary
        end
      end
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
