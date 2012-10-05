require 'json'
require 'mcollective'

module Orchestrator
  class Orchestrator
  include MCollective::RPC

    private
    def check_mcollective_result(stats)
      stats.each do |agent|
        status = agent.results[:statuscode]
        raise "MCollective call failed in agent: #{agent}" unless status == 0
      end
    end

    public
    def deploy(nodes)
      # TODO Check if nodes contains all required data
      nodes.each do |node|
        mc = rpcclient("nailyfact")
        mc.progress = false
        mc.discover(:nodes => [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}
        stats = mc.post(:value => metadata.to_json)
        check_mcollective_result(stats)
      end

      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      mc = rpcclient("puppetd")
      mc.progress = false
      mc.discover(:nodes => macs)
      stats = mc.runonce
      printrpc mc.status
      sleep 5
      printrpc mc.status
    end

    def verify_networks(args)
    end
  end

end
