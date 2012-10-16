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
      reporter = Naily::Reporter.new(@producer, data['respond_to'])
      @orchestrator.deploy(reporter, data['args']['task_uuid'], data['args']['nodes'])
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'])
      args = data['args']
      @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
    end
  end
end

