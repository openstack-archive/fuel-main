require 'mcollective'

module Astute
  class MClient
    include MCollective::RPC

    attr_accessor :retries

    def initialize(ctx, agent, nodes=nil, check_result=true, timeout=nil)
      @task_id = ctx.task_id
      @agent = agent
      @nodes = nodes.map { |n| n.to_s }
      @check_result = check_result
      @mc = rpcclient(agent, :exit_on_failure => false)
      @mc.timeout = timeout if timeout
      @mc.progress = false
      @retries = Astute.config.MC_RETRIES
      unless @nodes.nil?
        @mc.discover(:nodes => @nodes)
      end
    end

    def method_missing(method, *args)
      res = @mc.send(method, *args)
      if method == :discover
        @nodes = args[0][:nodes]
        return res
      end
      # Enable if needed. In normal case it eats the screen pretty fast
      log_result(res, method)
      return res unless @check_result
      
      err_msg = ''
      # Following error might happen because of misconfiguration, ex. direct_addressing = 1 only on client
      #  or.. could be just some hang? Let's retry if @retries is set
      if res.length < @nodes.length
        # some nodes didn't respond
        retry_index = 1
        while retry_index <= @retries
          sleep rand
          nodes_responded = res.map { |n| n.results[:sender] }
          not_responded = @nodes - nodes_responded
          Astute.logger.debug "Retry ##{retry_index} to run mcollective agent on nodes: '#{not_responded.join(',')}'"
          @mc.discover(:nodes => not_responded)
          new_res = @mc.send(method, *args)
          log_result(new_res, method)
          # new_res can have some nodes which finally responded
          res += new_res
          break if res.length == @nodes.length
          retry_index += 1
        end
        if res.length < @nodes.length
          nodes_responded = res.map { |n| n.results[:sender] }
          not_responded = @nodes - nodes_responded
          err_msg += "#{@task_id}: MCollective agents '#{not_responded.join(',')}' didn't respond.\n"
        end
      end
      failed = res.select { |x| x.results[:statuscode] != 0 }
      if failed.any?
        err_msg += "#{@task_id}: MCollective call failed in agent '#{@agent}', "\
                     "method '#{method}', failed nodes: #{failed.map{|x| x.results[:sender]}.join(',')}"
      end
      raise err_msg unless err_msg.empty?

      return res
    end

    private
    def log_result(result, method)
      result.each do |node|
        Astute.logger.debug "#{@task_id}: MC agent '#{node.agent}', method '#{method}', "\
                            "results: #{node.results.inspect}"
      end
    end

  end
end
