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
  Astute.logger = @logger

  def self.logger
    @logger
  end

  def self.logger=(logger)
    Astute.logger = logger
    @logger = logger
  end

end
