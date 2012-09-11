require 'naily/framework/async'
require 'naily/mcclient/simple'
require 'naily/mcclient/blocking'

module Naily
  module Handler
    class Mco
      
      def initialize args
        @logger = Logger.new(STDOUT)
        @logger.level = Logger::DEBUG
        @logger.debug("Initializing driver independent handler: Naily::Handler::Mco")
        
        @args = args
      end

      def handle &blk
        case @args["client"]
        when "simple"
          client = Naily::MCClient::Simple.new
        when "blocking"
          client = Naily::MCClient::Blocking.new
        else
          raise "Unknown mcollective client"
        end

        async = Naily::Framework::Async.new client
        
        async.call @args["action"], @args["action_args"] do |result|
          @logger.debug("Asynced call returned result: #{result}")
          yield({'result' => 'Action ended: #{result}'})
        end
      end
    end
  end
end
