require 'amqp'
require 'json'
require 'naily/amqp/helpers'
require 'naily/amqp/message'
require 'naily/amqp/topic_consumer'
require 'naily/amqp/direct_publisher'
require 'naily/amqp/handler'

# WE FOLLOW OPENSTACK RPC MODEL DESCRIBED HERE
# http://docs.openstack.org/developer/nova/devref/rpc.html

# RUBY AMQP RPC MODEL DESCRIBED HERE 
# http://rubyamqp.info/articles/patterns_and_use_cases/

module Naily
  module Amqp
    class Driver

      include Helpers

      def initialize options={}
        default_options = {
          :host => "localhost",
          :port => 5672,
          :username => "guest",
          :password => "guest",

          :topic_exchange_name => "nailgun.topic",
          :topic_queue_name => "mcollective",
          :topic_queue_routing_key => "mcollective",
        }
        opts = default_options.merge(options)

        logger.debug("Connecting to rabbitmq")
        AMQP.connect(:host => opts[:host], 
                     :port => opts[:port], 
                     :username => opts[:username], 
                     :password => opts[:password]) do |connection|
          @connection = connection
          logger.debug("Initializing channel")
          AMQP::Channel.new(connection) do |channel| 
            @channel = channel
            
            TopicConsumer.new(self,
                              channel,
                              opts[:topic_exchange_name],
                              opts[:topic_queue_name],
                              opts[:topic_queue_routing_key])
            
            
          end
        end
      end

      def handle message
        raise "Message is not valid" if not message.valid?
        handler = Naily::Amqp::Handler.new message 
        response = handler.handle
        DirectPublisher.new(@channel, response) if response
      end

      def disconnect &blk
        @connection.close
        yield if blk
      end

      # def ready? options={} &blk
      #   default_options = {
      #     :timeout => 10,
      #     :on_timeout => nil
      #   }
      #   options = default_options.merge(options)
      #   tick = 0.5
      #   n = 0

      #   timer = EM::PeriodicTimer.new(tick) do
      #     if @status == :ready
      #       timer.cancel
      #       yield true
      #     end
      #     if (n+=1) > options[:timeout] / tick
      #       @logger.error("Ready status timed out")
      #       timer.cancel
      #       if options[:on_timeout]
      #         options[:on_timeout].call if options[:on_timeout]
      #       else
      #         yield false
      #       end
      #     end
      #   end
      # end
      
    end
  end
end
