module Puppet::Parser::Functions
  newfunction(:ipcalc_network_count_addresses, :type => :rvalue, :doc => <<-EOS
Returns count of addresses of network.
    EOS
  ) do |arguments|

    require 'ipaddr'

    if (arguments.size != 2) then
      raise(Puppet::ParseError, "ipcalc_network_count_addresses(): Wrong number of arguments "+
            "given #{arguments.size} for 2")
    end

    begin
      ip = IPAddr.new("#{arguments[0]}/#{arguments[1]}")
    rescue ArgumentError
      raise(Puppet::ParseError, "ipcalc_network_count_addresses(): bad arguments #{arguments[0]} #{arguments[1]}")
    end

    return ip.to_range.to_a.size
  end
end
