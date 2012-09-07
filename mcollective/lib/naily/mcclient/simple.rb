require 'mcollective'
require 'naily/framework/client'

module Naily
  module MCClient
    class Simple
      include MCollective::RPC
      include Naily::Framework::Client

      def initialize
        @mc = rpcclient('naily')
        @mc.verbose = true
      end
      
      def run
        responses = []
        @mc.runonce().each do |response|
          responses << response
        end
      end

      def disconnect
        @mc.disconnect
      end
    end
  end
end
