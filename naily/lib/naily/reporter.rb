module Naily
  class Reporter
    def initialize(producer, method, task_uuid)
      @producer = producer
      @method = method
      @task_uuid = task_uuid
    end

    def report(msg)
      msg_with_task = {'task_uuid' => @task_uuid}.merge(msg)
      message = {'method' => @method, 'args' => msg_with_task}
      Naily.logger.info "Casting message to fuelweb: #{message.inspect}"
      @producer.publish(message)
    end
  end
end
