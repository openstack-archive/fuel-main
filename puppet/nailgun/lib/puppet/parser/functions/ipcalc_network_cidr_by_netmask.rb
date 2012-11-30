module Puppet::Parser::Functions
  newfunction(:ipcalc_network_cidr_by_netmask, :type => :rvalue, :doc => <<-EOS
Returns network cidr netmask by network netmask.
    EOS
  ) do |arguments|

    require 'ipaddr'

    if (arguments.size != 1) then
      raise(Puppet::ParseError, "ipcalc_network_cidr_by_netmask(): Wrong number of arguments "+
            "given #{arguments.size} for 1")
    end

    begin
      return arguments[0].to_s.split('.').map { |e| e.to_i.to_s(2).rjust(8,"0")}.join.count("1").to_s
    rescue ArgumentError
      raise(Puppet::ParseError, "ipcalc_network_cidr_by_netmask(): bad argument #{arguments[0]}")
    end
  end
end
