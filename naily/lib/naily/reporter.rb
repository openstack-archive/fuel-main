module Naily
  class Reporter
    def initialize(method)
      @method = method
    end

    def report(msg)
      p msg
      # TODO call rpc.cast with @method and this msg
    end
  end
end

