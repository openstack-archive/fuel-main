require 'json'
require 'naily/amqp/helpers'

module Naily
  module Amqp
    class Message
      include Helpers
      
      attr_accessor :header
      attr_accessor :body
      
      def valid?
        return false if not @body
      end
      
      def to_s
        JSON.dump(self.body)
      end
      
    end
    
    
    class Request < Message
      
      # HERE HEADER IS NOT AMQP HEADER BUT 
      # AMQP HEADER ATTRIBUTES. IT IS HASH
      
      def initialize h=nil, b=nil
        @header = h
        @body = b
      end
      
      def valid?
        return false if not @body
        return false if not @body["method"]
        return false if self.call? and not @body["msg_id"]
        true
      end
      
      def call?
        return true if @body["msg_id"]
        false
      end    
      
      def rpc_method
        return @body["method"]
      end
      
      def rpc_method_args
        return @body["args"]
      end
      
      def msg_id
        @body["msg_id"]
      end
      
    end
    
    class Response < Message
      
      attr_accessor :routing_key
      attr_accessor :exchange_name
    
      def initialize b=nil, options={}
        self.body = b
        self.routing_key = options[:routing_key] if options[:routing_key]
        self.exchange_name = options[:exchange_name] if options[:exchange_name]
      end
      
    end
  end
end
