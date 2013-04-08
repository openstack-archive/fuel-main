module Naily
  class Producer
    def initialize(exchange)
      @exchange = exchange
    end

    def publish(message, options={})
      default_options = {:routing_key => Naily.config.broker_publisher_queue,
                         :content_type => 'application/json'}
      options = default_options.merge(options)

      begin
        @exchange.publish(message.to_json, options)
      rescue
        Naily.logger.error "Error publishing message: #{$!}"
      end
    end
  end
end
