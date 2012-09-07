require 'rubygems'
require 'eventmachine'
require 'amqp'
require 'json'
require 'lib/helpers'


class MyClient

  include Helpers

  def initialize
    test_message_id = random_string
    test_message_payload = JSON.dump({"msg_id" => test_message_id,
                                       "action" => "status"})

    test_message_metadata = {
      :routing_key => "mcollective"
    }

    response_exname = test_message_id
    response_qname = test_message_id
    response_routing_key = test_message_id

    request_exname = "nailgun.topic"

    logger.debug("Connecting to rabbitmq")
    AMQP.connect(:host => "localhost", 
                 :port => 5672, 
                 :username => "guest", 
                 :password => "guest") do |connection|
      @connection = connection
      logger.debug("Initializing channel")
      AMQP::Channel.new(connection) do |channel|

        
        logger.debug("Initializing response exchange: #{response_exname}")
        response_exchange = AMQP::Exchange.new(channel, :direct, response_exname,
                                               :auto_delete => true)
        logger.debug("Initializing response queue: #{response_qname}")
        response_queue = AMQP::Queue.new(channel, response_qname, 
                                         :exclusive => true, :auto_delete => true)
        logger.debug("Binding response queue to response exchange")
        response_queue.bind(response_exchange, :routing_key => response_routing_key)

        logger.debug("Subscribing to response queue")
        response_queue.subscribe(:ack => true) do |metadata, payload|
          logger.debug("Response:")
          logger.debug("Response: metadata: #{metadata}")
          logger.debug("Response: payload: #{payload}")
          metadata.ack
          response_queue.purge
          response_queue.delete
          response_exchange.delete
          EM.stop
        end

        logger.debug("Initializing request exchange: #{request_exname}")
        request_exchange = AMQP::Exchange.new(channel, :topic, "nailgun.topic")

        logger.debug("Sending request: #{test_message_payload}")
        request_exchange.publish(test_message_payload, test_message_metadata)
      end
    end
  end

  def disconnect &blk
    @connection.close
    yield if blk
  end

end


EM.run do
  myclient = MyClient.new

  Signal.trap("TERM") do
    puts "TERM signal has been caught"
    myclient.disconnect do
      EventMachine.stop
    end
  end

  Signal.trap("INT") do
    puts "INT signal has been caught"
    myclient.disconnect do 
      EventMachine.stop 
    end
  end

end
