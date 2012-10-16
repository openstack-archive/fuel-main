require 'symboltable'
require 'singleton'

class SymbolTable
  include Singleton
end

module Naily
  class ConfigError < StandardError; end
  class UnknownOptionError < ConfigError
    attr_reader :name

    def initialize(name)
      super("Unknown config option #{name}")
      @name = name
    end
  end

  class ParseError < ConfigError
    attr_reader :line

    def initialize(message, line)
      super(message)
      @line = line
    end
  end

  def self.config
    config = SymbolTable.instance
    config.update(default_config) if config.empty?
    return config
  end

  def self.default_config
    conf = {}
    conf[:broker_host] = 'localhost'
    conf[:broker_port] = 5672
    conf[:broker_username] = 'guest'
    conf[:broker_password] = 'guest'

    conf[:broker_queue] = 'naily'
    conf[:broker_publisher_queue] = 'nailgun'
    conf[:broker_exchange] = 'nailgun'
    return conf
  end
end
