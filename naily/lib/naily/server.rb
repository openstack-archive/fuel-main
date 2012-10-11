require 'eventmachine'
require 'amqp'
require 'json'
require 'naily/dispatcher'

module Naily
  class Server
    attr_reader :options, :delegate

    def initialize(options)
      @options = options.dup.freeze
      @delegate = options[:delegate] || Dispatcher.new(@options)
    end

    def run
      EM.run do
        AMQP.logging = true
        @connection = AMQP.connect(connection_options)
        @channel = AMQP::Channel.new(@connection)
        @channel.on_error do |ch, error|
          Naily.logger.fatal "Channel error #{error}"
          stop
        end

        exchange = @channel.topic(options[:broker_exchange], :durable => true)

        queue = @channel.queue(options[:broker_queue], :durable => true)
        queue.bind(exchange, :routing_key => options[:broker_queue])

        queue.subscribe do |header, payload|
          Thread.new do
            dispatch payload
          end
        end

        Signal.trap('INT')  do
          Naily.logger.info "Got INT signal, stopping"
          stop
        end

        Signal.trap('TERM') do
          Naily.logger.info "Got TERM signal, stopping"
          stop
        end

        Naily.logger.info "Server started"
      end
    end

    def stop(&block)
      if @connection
        @connection.close { EM.stop(&block) }
      else
        EM.stop(&block)
      end
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

      unless delegate.respond_to?(data['method'])
        Naily.logger.error "Unsupported RPC call #{data['method']}"
        # TODO: send RPC error response
        return
      end

      Naily.logger.info "Processing RPC call #{data['method']}"

      begin
        result = delegate.send(data['method'], data)
      rescue
        Naily.logger.error "Error running RPC method #{data['method']}: #{$!}"
        # TODO: send RPC error response
        return
      end

      if data['msg_id']
        Naily.logger.info "Sending RPC call result #{result.inspect} for rpc call #{data['method']}"
        @channel.default_exchange.publish(JSON.dump(result), :routing_key => data['msg_id'])
      end
    end

    def connection_options
      {
        :host => options[:broker_host],
        :port => options[:broker_port],
        :username => options[:broker_username],
        :password => options[:broker_password],
      }.reject { |k, v| v.nil? }
    end
  end
end

