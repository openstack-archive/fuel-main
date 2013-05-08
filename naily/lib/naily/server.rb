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
      self
    end

  private

    def server_loop
      loop do
        consume_one do |payload|
          dispatch payload
        end
        Thread.stop
      end
    end

    def consume_one
      @consumer = AMQP::Consumer.new(@channel, @queue)
      @consumer.on_delivery do |metadata, payload|
        metadata.ack
        Thread.new do
          yield payload
          @loop.wakeup
        end
        @consumer.cancel
      end
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

      if Naily.config.empty_dispatch_message
        m = "empty_dispatch_message"
      else
        m = "dispatch_message"
      end

      if data.kind_of?(Array)
        Naily.logger.debug "Message seems to be an array"
        data.each do |message|
          Naily.logger.debug "Dispatching message: #{message.inspect}"
          self.send(m, message)
        end
      else
        Naily.logger.debug "Message seems to be plain message"
        Naily.logger.debug "Dispatching message: #{data.inspect}"
        self.send(m, data)
      end
    end

    def empty_dispatch_message(data)
      Naily.logger.debug "empty_dispatch_message called: #{data.inspect}"
    end

    def dispatch_message(data)

      Naily.logger.debug "dispatch_message called: #{data.inspect}"
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
