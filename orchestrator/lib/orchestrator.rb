require 'json'
require 'logger'

require 'orchestrator/orchestrator'

module Orchestrator
  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end

  VERSION = '0.0.1'
end
