module Astute
  class Context
    attr_accessor :task_id, :reporter, :deploy_log_parser

    def initialize(task_id, reporter, deploy_log_parser=nil)
      @task_id = task_id
      @reporter = reporter
      @deploy_log_parser = deploy_log_parser
    end
  end
end
