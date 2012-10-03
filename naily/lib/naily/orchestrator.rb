require 'mcollective'

module Naily
  class Orchestrator
  include MCollective::RPC
    def initialize(nodes, metadata={})
      @nodes = nodes
      @metadata = metadata
    end

    private
    def check_mcollective_result(stats)
      stats.each do |agent|
        status = agent.results[:statuscode]
        raise "MCollective call failed in agent: #{agent}" unless status == 0
      end
    end

    public
    def deploy
      mc = rpcclient("nailyfact")
      mc.progress = false
      mc.discover(:nodes => @nodes)
      stats = mc.post(:value => @metadata)
      check_mcollective_result(stats)

      mc = rpcclient("puppetd")
      mc.progress = false
      mc.discover(:nodes => @nodes)
      stats = mc.runonce
      printrpc mc.status
      sleep 5
      printrpc mc.status
    end
  end

end
