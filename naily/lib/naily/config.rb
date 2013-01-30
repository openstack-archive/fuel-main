require 'symboltable'
require 'singleton'

module Naily
  class ConfigError < StandardError; end
  class UnknownOptionError < ConfigError
    attr_reader :name

    def initialize(name)
      super("Unknown config option #{name}")
      @name = name
    end
  end

  class MyConfig
    include Singleton
    attr_reader :configtable

    def initialize
      # We need new instance of SymbolTable. If we use singleton for SymbolTable,
      #   the same instance will be used in Astute.
      @configtable = SymbolTable.new
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
    config = MyConfig.instance.configtable
    config.update(default_config) if config.empty?
    return config
  end

  def self.default_config
    conf = {}
    conf[:broker_host] = 'localhost'
    conf[:broker_port] = 5672
    conf[:broker_username] = 'mcollective'
    conf[:broker_password] = 'mcollective'

    conf[:broker_queue] = 'naily'
    conf[:broker_publisher_queue] = 'nailgun'
    conf[:broker_exchange] = 'nailgun'
    return conf
  end
end
