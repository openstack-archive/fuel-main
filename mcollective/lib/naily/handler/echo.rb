module Naily
  module Handler
    class Echo 

      def initialize args={}
        @args = args
      end

      def handle &blk
        yield @args
      end

    end
  end
end
