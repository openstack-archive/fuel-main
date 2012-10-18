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
      result = @orchestrator.deploy(reporter, data['args']['task_uuid'], data['args']['nodes'])
      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      args = data['args']
      result = @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end
  end
end

