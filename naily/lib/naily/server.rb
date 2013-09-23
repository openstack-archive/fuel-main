#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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
        messages = JSON.load(payload)
      rescue => ex
        Naily.logger.error "Error deserializing payload: #{ex.message}, trace: #{ex.backtrace.inspect}"
        # TODO: send RPC error response
        return
      end

      (messages.is_a?(Array) ? messages : [messages]).each_with_index do |message, i|
        begin
          dispatch_message message
        rescue StopIteration
          Naily.logger.debug "Dispatching aborted by #{message['method']}"
          abort_messages messages[(i + 1)..-1]
          break
        rescue => ex
          Naily.logger.error "Error running RPC method #{message['method']}: #{ex.message}, trace: #{ex.backtrace.inspect}"
          return_results message, {
            'status' => 'error',
            'error'  => "Error occurred while running method '#{message['method']}'. Inspect Orchestrator logs for the details."
          }
        end
      end
    end

    def dispatch_message(data)
      Naily.logger.debug "Dispatching message: #{data.inspect}"

      if Naily.config.fake_dispatch
        Naily.logger.debug "Fake dispatch"
        return
      end

      unless @delegate.respond_to?(data['method'])
        Naily.logger.error "Unsupported RPC call '#{data['method']}'"
        return_results data, {
          'status' => 'error',
          'error'  => "Unsupported method '#{data['method']}' called."
        }
        return
      end

      Naily.logger.info "Processing RPC call '#{data['method']}'"
      @delegate.send(data['method'], data)
    end

    def return_results(message, results)
      if results.is_a?(Hash) && message['respond_to']
        reporter = Naily::Reporter.new(@producer, message['respond_to'], message['args']['task_uuid'])
        reporter.report results
      end
    end

    def abort_messages(messages)
      return unless messages && messages.size > 0
      messages.each do |message|
        begin
          Naily.logger.debug "Aborting '#{message['method']}'"
          err_msg = {
            'status' => 'error',
            'error' => 'Task aborted',
            'progress' => 0,
          }

          if message['args']['nodes'].instance_of?(Array)
            err_nodes = message['args']['nodes'].map do |node|
              {'uid' => node['uid'], 'status' => 'error', 'error_type' => 'provision', 'progress' => 0}
            end

            err_msg.merge!('nodes' => err_nodes)
          end

          return_results(message, err_msg)
        rescue => ex
          Naily.logger.debug "Failed to abort '#{message['method']}': #{ex.inspect}"
        end
      end
    end
  end
end
