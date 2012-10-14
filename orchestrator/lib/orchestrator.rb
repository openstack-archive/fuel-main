require 'json'
require 'logger'

require 'orchestrator/orchestrator'
require 'orchestrator/mcollective'
require 'orchestrator/metadata'
require 'orchestrator/deployer'
require 'orchestrator/network'

module Orchestrator
  autoload 'Context', 'orchestrator/context'

  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end

  VERSION = '0.0.1'
end
