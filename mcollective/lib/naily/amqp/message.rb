require 'json'
require 'naily/amqp/helpers'

module Naily
  module Amqp
    class Message
      include Helpers

      attr_reader :metadata
      
      def payload= p
        @payload = JSON.parse(p)
      end
      
      def payload
        JSON.dump(@payload)
      end
      
      def valid?
        return false if not @payload
      end
      
      def to_s
        self.payload
      end
      
    end


    class Request < Message
      
      def initialize m=nil, p=nil
        @metadata = m
        self.payload = p
      end
      
      def valid?
        call_valid_actions = ["status"]
        cast_valid_actions = ["deploy"]
        return false if not @payload
        return false if not @payload["action"]
        return false if self.call? and not call_valid_actions.include?(self.action)
        return false if not self.call? and not cast_valid_actions.include?(self.action)
        return false if self.call? and not @payload["msg_id"]
        true
      end
      
      def call?
        return true if @payload["msg_id"]
        false
      end    
      
      def msg_id
        @payload["msg_id"]
      end
      
      def action
        @payload["action"]
      end
      
    end
    
    class Response < Message
      
      attr_accessor :routing_key
      attr_accessor :exchange_name
      
      def initialize p=nil, options={}
        self.payload = p
        self.routing_key = options[:routing_key] if options[:routing_key]
        self.exchange_name = options[:exchange_name] if options[:exchange_name]
      end
      
    end
  end
end
