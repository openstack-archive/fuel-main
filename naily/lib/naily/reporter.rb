module Naily
  class Reporter
    def initialize(producer, method, task_uuid)
      @producer = producer
      @method = method
      @task_uuid = task_uuid
    end

    def report(msg)
      message = {'method' => @method, 'task_uuid' => @task_uuid, 'args' => msg}
      Naily.logger.info "Casting message to nailgun: #{message.inspect}"
      @producer.publish(message)
    end
  end
end
