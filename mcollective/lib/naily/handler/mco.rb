require 'naily/framework/async'

module Naily
  module Handler
    class Mco
      
      def initialize args
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
          yield({'result' => 'Action ended: #{result}'})
        end
      end
    end
  end
end
