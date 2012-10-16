require 'json'

module Naily
  class Producer
    def initialize(channel, exchange)
      @channel = channel
      @exchange = exchange
      queue = @channel.queue("nailgun", :durable => true)
      queue.bind(@exchange, :routing_key => "nailgun")
    end

    def publish(message, options={})
      @exchange.publish(message, options)
    end
  end
end
