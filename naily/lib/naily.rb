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

  def self.logger
    @logger ||= Logger.new(STDOUT)
  end

  def self.logger=(logger)
    @logger = logger
  end
end
