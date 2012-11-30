module Puppet::Parser::Functions
  newfunction(:ipcalc_network_by_address_netmask, :type => :rvalue, :doc => <<-EOS
Returns network address by host ip address and netmask.
    EOS
  ) do |arguments|

    require 'ipaddr'

    if (arguments.size != 2) then
      raise(Puppet::ParseError, "ipcalc_network_by_address_netmask(): Wrong number of arguments "+
            "given #{arguments.size} for 2")
    end

    begin
      ip = IPAddr.new("#{arguments[0]}/#{arguments[1]}")
    rescue ArgumentError
      raise(Puppet::ParseError, "ipcalc_network_by_address_netmask(): bad arguments #{arguments[0]} #{arguments[1]}")
    end

    return ip.to_s
  end
end
