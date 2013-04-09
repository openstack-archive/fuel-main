require 'json'

module Naily
  class Server
    def initialize(channel, exchange, delegate, producer)
      @channel  = channel
      @exchange = exchange
      @delegate = delegate
      @producer = producer
    end

    def run
      @queue = @channel.queue(Naily.config.broker_queue, :durable => true)
      @queue.bind @exchange, :routing_key => Naily.config.broker_queue
      @loop = Thread.new(&method(:server_loop))
    end

  private

    def server_loop
      Naily.logger.info "Server loop started"
      begin
        loop do
          consume_one do |message|
            dispatch message
          end
          Thread.stop
        end
      rescue => ex
        Naily.logger.error "Exception in server loop: #{ex.inspect}"
      ensure
        Naily.logger.info "Server loop finished"
      end
    end

    def consume_one
      @consumer = AMQP::Consumer.new(@channel, @queue)
      @consumer.on_delivery do |message|
        Thread.new do
          yield message
          @loop.wakeup
        end
        @consumer.cancel
      end
      Naily.logger.info "Waiting for a message"
      @consumer.consume
    end

    def dispatch(payload)
      Naily.logger.debug "Got message with payload #{payload.inspect}"

      begin
        data = JSON.load(payload)
      rescue Exception => e
        Naily.logger.error "Error deserializing payload: #{e.message}, trace: #{e.backtrace.inspect}"
        # TODO: send RPC error response
        return
      end

      unless @delegate.respond_to?(data['method'])
        Naily.logger.error "Unsupported RPC call #{data['method']}"
        if data['respond_to']
          reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
          reporter.report({'status' => 'error', 'error' => "Unsupported method '#{data['method']}' called."})
        end
        return
      end

      Naily.logger.info "Processing RPC call #{data['method']}"

      begin
        @delegate.send(data['method'], data)
      rescue Exception => e
        Naily.logger.error "Error running RPC method #{data['method']}: #{e.message}, trace: #{e.backtrace.inspect}"
        if data['respond_to']
          reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
          reporter.report({'status' => 'error', 'error' => "Error occurred while running method '#{data['method']}'. See logs of Orchestrator for details."})
        end
      end
    end
  end
end
