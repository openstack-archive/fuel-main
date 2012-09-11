require 'logger'
require 'mcollective'
require 'naily/framework/client'

module Naily
  module MCClient
    class Simple
      include MCollective::RPC
      include Naily::Framework::Client

      def initialize
        @logger = Logger.new(STDOUT)
        @logger.level = Logger::DEBUG
        @logger.debug("Initializing mco client: Naily::MCClient::Simple")

        @mc = rpcclient('naily')
        @mc.verbose = true
      end
      
      def run *args
        @logger.debug("Client action: run")
        responses = []
        @mc.runonce().each do |response|
          responses << response
        end
        @logger.debug("Client action ended")
      end

      def disconnect
        @mc.disconnect
      end
    end
  end
end
