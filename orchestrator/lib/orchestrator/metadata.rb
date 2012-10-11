require 'json'
require 'mcollective'

module Orchestrator
  class FactsPublisher
    include MCollective::RPC
    include ::Orchestrator

    def post(reporter, nodes)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      ::Orchestrator.logger.debug "nailyfact - storing metadata for nodes: #{macs.join(',')}"

      nodes.each do |node|
        mc = rpcclient("nailyfact")
        mc.progress = false
        mc.discover(:nodes => [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = mc.post(:value => metadata.to_json)
        self.check_mcollective_result(stats)
      end
    end
  end
end

