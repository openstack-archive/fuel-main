require 'eventmachine'
require 'amqp'
require 'json'
require 'logger'
require 'naily/dispatcher'

module Naily
  class Server
    attr_reader :options, :delegate

    def initialize(config)
      @options = options.dup
      # TODO: validate options
      @config = config
      @options.freeze
      @delegate = options[:delegate] || Dispatcher.new
    end

    def run
      EM.run do
        AMQP.logging = true
        @connection = AMQP.connect(connection_options)
        @channel = AMQP::Channel.new(@connection)
        @channel.on_error do |ch, error|
          logger.fatal "Channel error #{error}"

          stop { exit }
        end

        queue = @channel.queue(options[:queue], :durable => true)

        queue.subscribe do |header, payload|
          dispatch payload
        end

        Signal.trap('INT')  { stop }
        Signal.trap('TERM') { stop }

        puts "Server started"
      end
    end

    def stop(&block)
      if @connection
        @connection.close { EM.stop(&block) }
      else
        EM.stop(&block)
      end
    end

    def logger
      @logger ||= ::Logger.new(STDOUT)
    end

    attr_writer :logger

    private

    def dispatch(payload)
      logger.debug "Got message with payload #{payload.inspect}"

      begin
        data = JSON.load(payload)
      rescue
        logger.error "Error deserializing payload: #{$!}"
        return
      end

      unless delegate.respond_to?(data['method'])
        logger.error "Unsupported RPC call #{data['method']}"
        return
      end

      logger.info "Processing RPC call #{data['method']}"

      begin
        result = delegate.send(data['method'], *data['args'])
      rescue
        logger.error "Error running RPC method #{data['method']}: #{$!}"
        # TODO: send error response in case of RPC call
        return
      end

      if data['msg_id']
        logger.info "Sending RPC call result #{result.inspect} for rpc call #{data['method']}"
        @channel.default_exchange.publish(JSON.dump(result), :routing_key => data['msg_id'])
      end
    end

    def connection_options
      {
        :host => options[:host],
        :port => options[:port],
        :username => options[:username],
        :password => options[:password],
      }.reject { |k, v| v.nil? }
    end
  end
end

