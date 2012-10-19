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
      nodes = data['args']['nodes']
      nodes_not_booted = nodes.map { |n| n['uid'] }
      begin
        Timeout::timeout(20 * 60) do  # 20 min for booting target OS
          while true
            types = @orchestrator.node_type(nodes)
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
      end

      orchestrate(data) do |reporter|
        @orchestrator.deploy(reporter, data['args']['task_uuid'], nodes)
      end
    end

    def verify_networks(data)
      args = data['args']
      orchestrate(data) do |reporter|
        @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
      end
    end

    private
    def orchestrate(data, &block)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])

      result = block.call(reporter)

      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end
  end
end

