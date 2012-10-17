require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new
      @producer = producer
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def deploy(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      @orchestrator.deploy(reporter, data['args']['task_uuid'], data['args']['nodes'])
      reporter.report({'status' => 'ready', 'progress' => 100})
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      args = data['args']
      @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
      reporter.report({'status' => 'ready', 'progress' => 100})
    end
  end
end

