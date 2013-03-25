require 'astute'
require 'naily/version'
require 'naily/config'

require 'logger'
require 'json'

module Naily
  autoload 'Worker', 'naily/worker'
  autoload 'Server', 'naily/server'
  autoload 'Producer', 'naily/producer'
  autoload 'Dispatcher', 'naily/dispatcher'
  autoload 'Reporter', 'naily/reporter'

  def self.logger
    @logger
  end

  def self.logger=(logger)
    Astute.logger = logger
    @logger       = logger
  end
end
