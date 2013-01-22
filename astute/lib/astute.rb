require 'json'
require 'logger'

require 'astute/logparser'
require 'astute/orchestrator'
require 'astute/metadata'
require 'astute/deployment_engine'
require 'astute/network'
require 'astute/puppetd'
require 'astute/rpuppet'
require 'astute/deployment_engine/simple_puppet'
require 'astute/deployment_engine/nailyfact'

module Astute
  autoload 'Context', 'astute/context'
  autoload 'MClient', 'astute/mclient'
  autoload 'ProxyReporter', 'astute/reporter'

  def self.logger
    @logger ||= Logger.new('/var/log/astute.log')
  end

  def self.logger=(logger)
    @logger = logger
  end
end
