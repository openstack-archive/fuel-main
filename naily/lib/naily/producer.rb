require 'json'

module Naily
  class Producer
    def initialize(channel, exchange)
      @channel = channel
      @exchange = exchange
      queue = @channel.queue(Naily.config.broker_publisher_queue, :durable => true)
      queue.bind(@exchange, :routing_key => Naily.config.broker_publisher_queue)
    end

    def publish(message, options={})
      default_options = {:routing_key => Naily.config.broker_publisher_queue}
      options = default_options.merge(options)
      @exchange.publish(message, options)
    end
  end
end
