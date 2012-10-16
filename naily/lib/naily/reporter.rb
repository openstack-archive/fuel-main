module Naily
  class Reporter
    def initialize(producer, method)
      @producer = producer
      @method = method
    end

    def report(msg)
      message = {'method' => @method, 'args' => msg}
      Naily.logger.info "Casting message to nailgun: #{message.inspect}"
      @producer.publish(message, :routing_key => 'nailgun')
    end
  end
end
