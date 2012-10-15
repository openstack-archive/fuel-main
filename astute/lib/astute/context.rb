module Astute
  class Context
    attr_accessor :task_id, :reporter

    def initialize(task_id, reporter)
      @task_id = task_id
      @reporter = reporter
    end
  end
end
