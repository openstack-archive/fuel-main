require 'naily/handler/echo'
require 'naily/handler/null'
require 'naily/handler/mco'
require 'naily/amqp/message'

module Naily
  module Amqp
    class Handler
      include Helpers

      def initialize message
        logger.debug("Initializing driver dependent handler: Naily::Amqp::Handler")
        @message = message
        @real_handler = get_real_handler
      end
      
      def get_real_handler
        logger.debug("RPC method: #{@message.rpc_method}")
        case @message.rpc_method.to_sym
        when :echo
          return Naily::Handler::Echo.new @message.rpc_method_args
        when :mco
          return Naily::Handler::Mco.new @message.rpc_method_args
        else
          return Naily::Handler::Null.new @message.rpc_method_args
        end
      end

      def handle
        logger.debug("Handler request: #{@message}")
        @real_handler.handle do |response|
          logger.debug("Handler response: #{response}")
          response ||= {}
          if @message.call?
            body = {
              :result => response,
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
