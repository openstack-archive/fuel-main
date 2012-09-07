require 'rubygems'
require 'eventmachine'
require 'amqp'
require 'json'
require 'lib/helpers'


class MyServer

  include Helpers

  def initialize

    logger.debug("Connecting to rabbitmq")
    AMQP.connect(:host => "localhost", 
                 :port => 5672, 
                 :username => "guest", 
                 :password => "guest") do |connection|
      @connection = connection
      logger.debug("Initializing channel")
      AMQP::Channel.new(connection) do |channel|
        server_exchange = AMQP::Exchange.new(channel, :topic, "nailgun.topic")

        server_queue = AMQP::Queue.new(channel, "mcollective",
                                       :exclusive => true, :auto_delete => true)
        server_queue.bind(server_exchange, :routing_key => "mcollective")

        server_queue.subscribe() do |metadata, payload|
          logger.debug("Received message: #{payload}")

          payload_parsed = JSON.parse(payload) 
          msg_id = payload_parsed["msg_id"]
          exchange = AMQP::Exchange.new(channel, :direct, msg_id,
                                        :auto_delete => true)
          exchange.publish("Response", :routing_key => msg_id)
        end
      end
    end
  end

  def disconnect &blk
    @connection.close
    yield if blk
  end

end


EM.run do
  myserver = MyServer.new
  
  Signal.trap("TERM") do
    puts "TERM signal has been caught"
    myserver.disconnect do
      EventMachine.stop
    end
  end

  Signal.trap("INT") do
    puts "INT signal has been caught"
    myserver.disconnect do 
      EventMachine.stop 
    end
  end

end
