module Orchestrator
  def check_mcollective_result(stats, task_id="", log=true)
    # Following error might happen because of misconfiguration, ex. direct_addressing = 1 only on client
    raise "#{task_id}: MCollective has failed and didn't even return anything. Check it's logs." if stats.length == 0
    result_data = []
    stats.each do |agent|
      status = agent.results[:statuscode]
      result_data << agent.results['data']
      if status != 0
        raise "#{task_id}: MCollective call failed in agent '#{agent.agent}', results: #{agent.results.inspect}"
      else
        ::Orchestrator.logger.debug "#{task_id}: MC agent #{agent.agent} succeeded, results: #{agent.results.inspect}" if log
      end
    end
    return result_data
  end
end
