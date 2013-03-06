require 'rubygems'

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
  autoload 'NodesRemover', 'astute/nodes_remover'
  autoload 'Node', 'astute/node'
  autoload 'NodesHash', 'astute/node'
  LogParser.autoload :ParseDeployLogs, 'astute/logparser/deployment'
  LogParser.autoload :ParseProvisionLogs, 'astute/logparser/provision'
  LogParser.autoload :Patterns, 'astute/logparser/parser_patterns'

  def self.logger
    @logger ||= Logger.new('/var/log/astute.log')
    @logger.formatter = proc {|severity, datetime, progname, msg|
      severity_map = {'DEBUG' => 'debug', 'INFO' => 'info', 'WARN' => 'warning',
        'ERROR' => 'err', 'FATAL' => 'crit'}
      "#{datetime.strftime("%Y-%m-%dT%H:%M:%S")} #{severity_map[severity]}: #{msg}\n"
    }
    @logger
  end

  def self.logger=(logger)
    @logger = logger
  end

  config_file = '/opt/astute/astute.conf'
  Astute.config.update(YAML.load(File.read(config_file))) if File.exists?(config_file)
end
