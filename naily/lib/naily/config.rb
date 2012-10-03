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
      config = new
      File.open(path) do |f|
        f.each_line do |line|
          line.gsub!(/#.*$/, '').trim! # remove comments
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
      config[:host] = 'localhost'
      config[:port] = 5672
      config[:username] = 'guest'
      config[:password] = 'guest'
      config[:queue] = 'naily'
      config
    end
  end
end

