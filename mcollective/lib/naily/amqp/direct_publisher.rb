require 'amqp'
require 'naily/amqp/helpers'

module Naily
  module Amqp
    class DirectPublisher
      include Helpers
      
      def initialize channel, message
        logger.debug("Publish message: payload: #{message}")
        AMQP::Exchange.new(channel, :direct, message.exchange_name,
                           :auto_delete => true) do |exchange|
          exchange.publish(message, :routing_key => message.routing_key) do
            logger.debug("Publish message: complete")
          end
        end
      end
    end
  end
end
