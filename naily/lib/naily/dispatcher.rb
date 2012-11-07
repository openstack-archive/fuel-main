require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new
      @producer = producer
      @default_result = {'status' => 'ready', 'progress' => 100}
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def deploy(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      nodes_not_booted = nodes.map { |n| n['uid'] }
      begin
        Timeout::timeout(20 * 60) do  # 20 min for booting target OS
          while true
            types = @orchestrator.node_type(reporter, data['args']['task_uuid'], nodes)
            if types.length == nodes.length and types.all? {|n| n['node_type'] == 'target'}
              break
            end
            nodes_not_booted = nodes.map { |n| n['uid'] } - types.map { |n| n['uid'] }
            sleep 5
          end
        end
      rescue Timeout::Error
        error_msg = "Timeout of booting is exceeded for nodes: '#{nodes_not_booted.join(',')}'"
        reporter.report({'status' => 'error', 'error' => error_msg})
        return
      end

      result = @orchestrator.deploy(reporter, data['args']['task_uuid'], nodes)
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
