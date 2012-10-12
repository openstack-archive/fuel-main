require 'json'
require 'mcollective'

module Orchestrator
  class FactsPublisher
    include MCollective::RPC
    include ::Orchestrator

    def post(reporter, task_id, nodes)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      ::Orchestrator.logger.debug "#{task_id}: nailyfact - storing metadata for nodes: #{macs.join(',')}"

      nodes.each do |node|
        mc = rpcclient("nailyfact")
        mc.progress = false
        mc.discover(:nodes => [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = mc.post(:value => metadata.to_json)
        self.check_mcollective_result(stats, task_id)
      end
    end
  end
end

