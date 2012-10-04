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

  class Config
    def self.load(path)
      config = {}
      File.open(path) do |f|
        f.each_line do |line|
          line = line.gsub(/#.*$/, '').strip # remove comments
          next if line == ''

          unless /(\S+)\s*=\s*(\S.*)/ =~ line
            raise ConfigParseErorr.new("Syntax error in line #{line}", line)
          end

          name, value = $1, $2

          # TODO: validate config option
          # raise UnknownOptionError.new(name) unless config.respond_to?(:"#{name}=")

          config[name.to_sym] = value
        end
      end
      config
    end

    def self.default
      config = {}
      config[:broker_host] = 'localhost'
      config[:broker_port] = 5672
      config[:broker_username] = 'guest'
      config[:broker_password] = 'guest'

      config[:broker_queue] = 'naily'
      config[:broker_exchange] = 'naily'
      config
    end
  end
end

