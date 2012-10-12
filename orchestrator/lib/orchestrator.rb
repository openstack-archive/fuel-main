require 'json'
require 'logger'

require 'orchestrator/orchestrator'
require 'orchestrator/helpers'

module Orchestrator
  autoload 'PuppetPollingDeployer', 'orchestrator/deployer'
  autoload 'FactsPublisher', 'orchestrator/metadata'

  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end

  VERSION = '0.0.1'
end
