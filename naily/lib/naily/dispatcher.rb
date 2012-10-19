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
      orchestrate(data) do |reporter|
        @orchestrator.deploy(reporter, data['args']['task_uuid'], data['args']['nodes'])
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

