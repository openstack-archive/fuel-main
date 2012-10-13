require 'json'
require 'logger'

require 'orchestrator/orchestrator'
require 'orchestrator/mcollective'

module Orchestrator
  autoload 'PuppetPollingDeployer', 'orchestrator/deployer'
  autoload 'FactsPublisher', 'orchestrator/metadata'
  autoload 'Network', 'orchestrator/network'

  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end

  VERSION = '0.0.1'
end
