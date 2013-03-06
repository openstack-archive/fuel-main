require 'symboltable'
require 'singleton'

module Astute
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
    conf[:PUPPET_TIMEOUT] = 60*60        # maximum time it waits for the whole deployment
    conf[:PUPPET_DEPLOY_INTERVAL] = 2    # sleep for ## sec, then check puppet status again
    conf[:PUPPET_FADE_TIMEOUT] = 60      # How long it can take for puppet to exit after dumping to last_run_summary
    conf[:MC_RETRIES] = 5                # MClient tries to call mcagent before failure
    conf[:MC_RETRY_INTERVAL] = 1         # MClient sleeps for ## sec between retries
    conf[:PUPPET_FADE_INTERVAL] = 1      # Retry every ## seconds to check puppet state if it was running
    return conf
  end
end
