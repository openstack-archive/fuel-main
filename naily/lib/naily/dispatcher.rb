require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new(nil, log_parsing=true)
      @producer = producer
      @default_result = {'status' => 'ready', 'progress' => 100}
      @provisionLogParser = Astute::LogParser::ParseProvisionLogs.new
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def provision(data)
      Naily.logger.info("'provision' method called with data: #{data.inspect}")

      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])

      begin
        Naily.logger.info("Trying to instantiate cobbler engine: #{data['args']['engine'].inspect}")
        engine = Astute::Provision::Cobbler.new(data['args']['engine'])
      rescue
        Naily.logger.error("Error occured during cobbler initializing")
        reporter.report({
                          'status' => 'error',
                          'error' => 'Cobbler can not be initialized',
                          'progress' => 100
                        })
      end

      begin
        data['args']['nodes'].each do |node|
          Naily.logger.info("Adding #{node['name']} into cobbler")
          engine.item_from_hash('system', node['name'], node,
                           :item_preremove => true)
          engine.power_reboot(node['name'])
        end
      rescue
        reporter.report({
                          'status' => 'error',
                          'error' => 'Cobbler error',
                          'progress' => 100
                        })
        return
      end
      engine.sync
      report_result({}, reporter)
    end

    def deploy(data)
      Naily.logger.info("'deploy' method called with data: #{data.inspect}")

      # Following line fixes issues with uids: it should always be string
      data['args']['nodes'].map { |x| x['uid'] = x['uid'].to_s }
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      nodes_uids = nodes.map { |n| n['uid'] }
      time = Time::now.to_f
      nodes_not_booted = nodes.map { |n| n['uid'] }
      Naily.logger.info "Starting OS provisioning for nodes: #{nodes_not_booted.join(',')}"
      begin
        @provisionLogParser.prepare(nodes)
      rescue Exception => e
        Naily.logger.warn "Some error occurred when prepare LogParser: #{e.message}, trace: #{e.backtrace.inspect}"
      end
      time = 10 + time - Time::now.to_f
      sleep (time) if time > 0 # Wait while nodes going to reboot. Sleep not greater than 10 sec.
      begin
        Timeout::timeout(45 * 60) do  # 45 min for booting target OS
          while true
            time = Time::now.to_f
            types = @orchestrator.node_type(reporter, data['args']['task_uuid'], nodes, 2)
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
              Naily.logger.warn "Some error occurred when parse logs for nodes progress: #{e.message}, trace: #{e.backtrace.inspect}"
            end
            time = 5 + time - Time::now.to_f
            sleep (time) if time > 0 # Sleep not greater than 5 sec.
          end
          # We are here if jumped by break from while cycle
        end
      rescue Timeout::Error
        msg = "Timeout of provisioning is exceeded."
        Naily.logger.error msg
        error_nodes = nodes_not_booted.map { |n| {'uid' => n,
                                                  'status' => 'error',
                                                  'error_msg' => msg,
                                                  'progress' => 100,
                                                  'error_type' => 'provision'} }
        reporter.report({'status' => 'error', 'error' => msg, 'nodes' => error_nodes})
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
      result = @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'])
      report_result(result, reporter)
    end

    def remove_nodes(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      provision_engine = Astute::Provision::Cobbler.new(data['args']['provision_engine'])
      data['args']['provision_nodes'].each do |name|
        if provision_engine.system_exists(name)
          Naily.logger.info("Removing system from cobbler: #{name}")
          provision_engine.remove_system(name)
        end
      end
      provision_engine.sync
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
