module Naily
  module Server
    module Config
      extend self
      
      attr_accessor :driver
      attr_accessor :amqp_host
      attr_accessor :amqp_port
      attr_accessor :amqp_username
      attr_accessor :amqp_password
      attr_accessor :topic_exchange_name
      attr_accessor :topic_queue_name
      attr_accessor :topic_queue_routing_key
      
      def define
        yield self
      end
    end
  end
end
