require 'amqp'
require 'json'
require 'naily/amqp/helpers'

module Naily
  module Amqp
    class TopicConsumer

      include Helpers
      
      def initialize parent, channel, exchange_name, queue_name, routing_key, &blk
        logger.debug("Initializing topic consumer: exchange: #{exchange_name} "\
                     "queue: #{queue_name} routing_key: #{routing_key}")
        @parent = parent
        AMQP::Exchange.new(channel, :topic, exchange_name, 
                           :auto_delete => false, :durable => false) do |exchange|
          logger.debug("Exchange has been declared: #{exchange.name}")
          AMQP::Queue.new(channel, queue_name, :exclusive => true, 
                          :auto_delete => true) do |queue|
            logger.debug("Queue has been declared: #{queue.name}")
            queue.bind(exchange, :routing_key => routing_key) do
              logger.debug("Queue: #{queue.name} has been bound "\
                           "to exchange: #{exchange.name}")
              queue.subscribe(:ack => true) do |header, body|
                logger.debug("Received message: #{body}")
                message = Request.new(header.to_hash, JSON.load(body))
                if message.valid?
                  logger.debug("Message valid. Handling.")
                  @parent.handle(message)
                else
                  logger.error("Received message is not valid")
                end
                header.ack
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
