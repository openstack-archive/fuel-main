require 'naily/handler/echo'
require 'naily/handler/null'
require 'naily/handler/mco'
require 'naily/amqp/message'

module Naily
  module Amqp
    class Handler
      include Helpers

      def initialize message
        @message = message
        @real_handler = get_real_handler

      end
      
      def get_real_handler
        case message.rpc_method.to_sym
        when :echo
          return Naily::Handler::Echo.new @message.rpc_method_args.to_hash
        when :mco
          return Naily::Handler::Mco.new @message.rpc_method_args.to_hash
        else
          return Naily::Handler::Null.new @message.rpc_method_args.to_hash
        end
      end

      def handle
        @real_handler.handle do |response|
          response ||= {}
          if @message.call?
            body = {
              :result => handler_response,
              :failure => nil,
              :ending => false
            }
            options = {
              :exchange_name => @message.msg_id,
              :routing_key => @message.msg_id
            }
            return Response.new body, options
          end
          return nil
        end
      end
    end
  end
end
