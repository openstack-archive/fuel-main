require 'json'
require 'logger'

require 'astute/config'
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
  autoload 'NodeRemoval', 'astute/node_removal'

  def self.logger
    @logger ||= Logger.new('/var/log/astute.log')
    @logger.formatter = proc {|severity, datetime, progname, msg|
      "#{datetime.strftime("%Y-%m-%dT%H:%M:%S")} #{severity.downcase}: #{msg}\n"
    }
    @logger
  end

  def self.logger=(logger)
    @logger = logger
  end

  config_file = '/opt/astute/astute.conf'
  Astute.config.update(YAML.load(File.read(config_file))) if File.exists?(config_file)
end
