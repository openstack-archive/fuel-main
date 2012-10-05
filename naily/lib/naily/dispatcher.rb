

module Naily
  class Dispatcher
    attr_reader :options

    def initialize(options={})
      @options = options.dup.freeze
      @orchestrator = Orchestrator::Orchestrator.new
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def deploy(args)
      @orchestrator.deploy(args['nodes'])
    end

    def verify_networks(args)
      @orchestrator.verify_networks(args)
    end
  end
end

