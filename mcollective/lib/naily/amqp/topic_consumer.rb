require 'amqp'
require 'naily/amqp/helpers'

module Naily
  module Amqp
    class TopicConsumer

      include Helpers
      
      def initialize parent, channel, exchange_name, queue_name, routing_key, &blk
        logger.debug("Initializing topic consumer: exchange: #{exchange_name} "\
                     "queue: #{queue_name} routing_key: #{routing_key}")
        @parent = parent
        AMQP::Exchange.new(channel, :topic, exchange_name) do |exchange|
          AMQP::Queue.new(channel, queue_name, :exclusive => true, 
                          :auto_delete => true) do |queue|
            queue.bind(exchange, :routing_key => routing_key) do
              queue.subscribe(:ack => true) do |metadata, payload|
                message = Request.new(metadata, payload)
                logger.debug("Received message: #{message}")
                if message.valid?
                  @parent.handle(message)
                else
                  logger.error("Received message is not valid")
                end
                metadata.ack
              end
              if blk
                yield self
              end
            end
          end
        end
      end
    end
  end
end
