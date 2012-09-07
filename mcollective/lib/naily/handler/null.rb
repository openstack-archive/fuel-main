require 'naily/framework/async'

module Naily
  module Handler
    class Null
      
      def initialize args
      end

      def handle &blk
        yield
      end

    end
  end
end
