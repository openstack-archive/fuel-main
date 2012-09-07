require 'eventmachine'

module Naily
  module Framework
    class Async

      def initialize instance
        @instance = instance
      end

      def call method_name, *args, &blk
        EM.defer(Proc.new {
                   method = @instance.method(method_name)
                   method.call(*args)
                 }, blk ? blk : nil)
      end
    end
  end
end


