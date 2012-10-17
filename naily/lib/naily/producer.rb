require 'json'

module Naily
  class Producer
    def initialize(channel, exchange)
      @channel = channel
      @exchange = exchange
      begin
        queue = @channel.queue(Naily.config.broker_publisher_queue, :durable => true)
        queue.bind(@exchange, :routing_key => Naily.config.broker_publisher_queue)
      rescue
        Naily.logger.error "Error creating AMQP queue: #{$!}"
      end
    end

    def publish(message, options={})
      default_options = {:routing_key => Naily.config.broker_publisher_queue}
      options = default_options.merge(options)

      begin
        @exchange.publish(message, options)
      rescue
        Naily.logger.error "Error publishing message: #{$!}"
      end
    end
  end
end
