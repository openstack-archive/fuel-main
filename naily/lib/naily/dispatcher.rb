require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new
      @producer = producer
      @default_result = {'status' => 'ready', 'progress' => 100}
      @pattern_spec = {'type' => 'pattern-list', 'chunk_size' =>  40000, # Size of block which reads for pattern searching.
        'pattern_list' => [
          {'pattern' => 'Running kickstart %%pre script', 'progress' => 0.08},
          {'pattern' => 'to step enablefilesystems', 'progress' => 0.09},
          {'pattern' => 'to step reposetup', 'progress' => 0.13},
          {'pattern' => 'to step installpackages', 'progress' => 0.16},
          {'pattern' => 'Installing',
            'number' => 210, # Now it install 205 packets. Add 5 packets for growth in future.
            'p_min' => 0.16, # min percent
            'p_max' => 0.87 # max percent
            },
          {'pattern' => 'to step postinstallconfig', 'progress' => 0.87},
          {'pattern' => 'to step dopostaction', 'progress' => 0.92},
          ].reverse
        }
      @provisionLogParser = Astute::LogParser::ParseNodeLogs.new('install/anaconda.log', @pattern_spec)
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def deploy(data)
      # Following line fixes issues with uids: it should always be string
      data['args']['nodes'].map { |x| x['uid'] = x['uid'].to_s }
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      nodes_uids = nodes.map { |n| n['uid'] }
      time = Time::now.to_f
      nodes_not_booted = nodes.map { |n| n['uid'] }
      Naily.logger.info "Starting OS provisioning for nodes: #{nodes_not_booted.join(',')}" 
      begin
        @provisionLogParser.add_separator(nodes)
      rescue Exception => e
        Naily.logger.warn "Some error occured when add separator to logs: #{e.message}, trace: #{e.backtrace.inspect}"
      end
      time = 10 + time - Time::now.to_f
      sleep (time) if time > 0 # Wait while nodes going to reboot. Sleep not greater than 10 sec.
      begin
        Timeout::timeout(45 * 60) do  # 45 min for booting target OS
          while true
            time = Time::now.to_f
            types = @orchestrator.node_type(reporter, data['args']['task_uuid'], nodes, 5)
            target_uids = types.reject{|n| n['node_type'] != 'target'}.map{|n| n['uid']}
            Naily.logger.debug "Not provisioned: #{nodes_not_booted.join(',')}, got target OSes: #{target_uids.join(',')}" 
            if nodes.length == target_uids.length
              Naily.logger.info "All nodes #{target_uids.join(',')} are provisioned."
              break
            end
            nodes_not_booted = nodes_uids - types.map { |n| n['uid'] }
            begin
              nodes_progress = @provisionLogParser.progress_calculate(nodes_uids, nodes)
              nodes_progress.each do |n|
                if target_uids.include?(n['uid'])
                  n['progress'] = 100
                  # TODO(mihgen): should we change status only once?
                  n['status'] = 'provisioned'
                end
              end
              reporter.report({'nodes' => nodes_progress})
            rescue Exception => e
              Naily.logger.warn "Some error occured when parse logs for nodes progress: #{e.message}, trace: #{e.backtrace.inspect}"
            end
            time = 5 + time - Time::now.to_f
            sleep (time) if time > 0 # Sleep not greater than 5 sec.
          end
          # We are here if jumped by break from while cycle
        end
      rescue Timeout::Error
        Naily.logger.error "Provisioning has timed out"
        error_msg = "Timeout of provisioning is exceeded for nodes: '#{nodes_not_booted.join(',')}'"
        error_nodes = nodes_not_booted.map { |n| {'uid' => n,
                                                  'status' => 'error',
                                                  'progress' => 100,
                                                  'error_type' => 'provision'} }
        reporter.report({'status' => 'error', 'error' => error_msg, 'nodes' => error_nodes})
        return
      end

      nodes_progress = nodes.map do |n|
        {'uid' => n['uid'], 'progress' => 100, 'status' => 'provisioned'}
      end
      reporter.report({'nodes' => nodes_progress})

      result = @orchestrator.deploy(reporter, data['args']['task_uuid'], nodes, data['args']['attributes'])
      report_result(result, reporter)
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      args = data['args']
      result = @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
      report_result(result, reporter)
    end

    def remove_nodes(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      result = @orchestrator.remove_nodes(reporter, data['args']['task_uuid'], nodes)
      report_result(result, reporter)
    end

    private
    def report_result(result, reporter)
      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end
  end
end
