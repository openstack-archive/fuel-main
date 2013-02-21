require 'json'
require 'thread'

module Naily
  class Server
    def initialize(channel, exchange, delegate, producer)
      @channel  = channel
      @exchange = exchange
      @delegate = delegate
      @producer = producer
    end

    def run
      queue = @channel.queue(Naily.config.broker_queue, :durable => true)
      queue.bind(@exchange, :routing_key => Naily.config.broker_queue)

      semaphore = Mutex.new
      queue.subscribe do |header, payload|
        Thread.new do
          Thread.current['semaphore'] = semaphore
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
        result = @delegate.send(data['method'], data)
      rescue Exception => e
        Naily.logger.error "Error running RPC method #{data['method']}: #{e.message}, trace: #{e.backtrace.inspect}"
        if data['respond_to']
          reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
          reporter.report({'status' => 'error', 'error' => "Error occurred while running method '#{data['method']}'. See logs of Orchestrator for details."})
        end
        return
      end
    end
  end
end
