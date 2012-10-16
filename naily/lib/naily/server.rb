require 'json'

module Naily
  class Server
    attr_reader :options

    def initialize(options, channel, exchange, delegate)
      @options  = options.dup.freeze
      @channel  = channel
      @exchange = exchange
      @delegate = delegate
    end

    def run
      queue = @channel.queue(@options[:broker_queue], :durable => true)
      queue.bind(@exchange, :routing_key => @options[:broker_queue])

      queue.subscribe do |header, payload|
        Thread.new do
          dispatch payload
        end
      end

      Naily.logger.info "Server started"
    end

    private

    def dispatch(payload)
      Naily.logger.debug "Got message with payload #{payload.inspect}"

      begin
        data = JSON.load(payload)
      rescue
        Naily.logger.error "Error deserializing payload: #{$!}"
        # TODO: send RPC error response
        return
      end

      unless @delegate.respond_to?(data['method'])
        Naily.logger.error "Unsupported RPC call #{data['method']}"
        # TODO: send RPC error response
        return
      end

      Naily.logger.info "Processing RPC call #{data['method']}"

      begin
        result = @delegate.send(data['method'], data)
      rescue
        Naily.logger.error "Error running RPC method #{data['method']}: #{$!}"
        # TODO: send RPC error response
        return
      end

    end

  end
end

