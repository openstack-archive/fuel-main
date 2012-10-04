module Naily
  class Dispatcher
    attr_reader :options

    def initialize(options={})
      @options = options.dup.freeze
    end

    def echo(*args)
      Naily.logger.info 'Running echo command'
      args
    end
  end
end

