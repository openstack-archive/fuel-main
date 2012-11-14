require 'rubygems'
require 'json'

module Puppet::Parser::Functions
  newfunction(:json2array, :type => :rvalue, :doc => <<-EOS
Converts JSON to simple array.
    EOS
  ) do |arguments|

    raise(Puppet::ParseError, "json2array(): Wrong number of arguments " +
      "given (#{arguments.size} for 1)") if arguments.size < 1

    value = arguments[0]
    result = JSON.parse(value)
    return result

  end
end
