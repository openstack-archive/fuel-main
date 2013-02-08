require 'astute'
require 'naily/version'
require 'naily/config'

require 'logger'
require 'json'

module Naily
  autoload 'Server', 'naily/server'
  autoload 'Producer', 'naily/producer'
  autoload 'Dispatcher', 'naily/dispatcher'
  autoload 'Reporter', 'naily/reporter'

  @logger ||= Logger.new(STDOUT)
  @logger.formatter = proc {|severity, datetime, progname, msg|
    severity_map = {'DEBUG' => 'debug', 'INFO' => 'info', 'WARN' => 'warning',
      'ERROR' => 'err', 'FATAL' => 'crit'}
    "#{datetime.strftime("%Y-%m-%dT%H:%M:%S")} #{severity_map[severity]}: #{msg}\n"
  }
  Astute.logger = @logger

  def self.logger
    @logger
  end

  def self.logger=(logger)
    Astute.logger = logger
    @logger = logger
  end

end
