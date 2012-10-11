module Orchestrator
  def check_mcollective_result(stats, log=true)
    # Following error might happen because of misconfiguration, ex. direct_addressing = 1 only on client
    raise "MCollective has failed and didn't even return anything. Check it's logs." if stats.length == 0
    result_data = []
    stats.each do |agent|
      status = agent.results[:statuscode]
      result_data << agent.results['data']
      if status != 0
        raise "MCollective call failed in agent '#{agent.agent}', results: #{agent.results.inspect}"
      else
        ::Orchestrator.logger.debug "MC agent #{agent.agent} succeeded, results: #{agent.results.inspect}" if log
      end
    end
    return result_data
  end
end
