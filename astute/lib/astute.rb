require 'json'
require 'logger'

require 'astute/orchestrator'
require 'astute/mclient'
require 'astute/metadata'
require 'astute/deployer'
require 'astute/network'

module Astute
  autoload 'Context', 'astute/context'

  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end
end
