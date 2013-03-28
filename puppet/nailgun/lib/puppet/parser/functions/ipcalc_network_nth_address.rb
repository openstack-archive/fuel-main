module Puppet::Parser::Functions
  newfunction(:ipcalc_network_nth_address, :type => :rvalue, :doc => <<-EOS
Returns N-th address of network.
    EOS
  ) do |arguments|

    require 'ipaddr'

    if (arguments.size != 3) then
      raise(Puppet::ParseError, "ipcalc_network_nth_address(): Wrong number of arguments "+
            "given #{arguments.size} for 3")
    end

    begin
      ip = IPAddr.new("#{arguments[0]}/#{arguments[1]}")
    rescue ArgumentError
      raise(Puppet::ParseError, "ipcalc_network_nth_address(): bad arguments #{arguments[0]} #{arguments[1]} #{arguments[2]}")
    end

    if arguments[2].to_s =~ /^last$/
      return ip.to_range.to_a[-2].to_s
    elsif arguments[2].to_s =~ /^first$/
      return ip.to_range.to_a[1].to_s
    else
      return ip.to_range.to_a[arguments[2].to_i].to_s
    end
  end
end
