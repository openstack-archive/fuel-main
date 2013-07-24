#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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
      Naily.logger.info "Casting message to fuel: #{message.inspect}"
      @producer.publish(message)
    end
  end
end
