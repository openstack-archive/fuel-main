require 'ipaddr'

module Cobbler
  def self.find_by_ip(ipaddr, chefnode)

    interfaces = chefnode[:network][:interfaces]

    # Here we are iterating over all node interfaces
    interfaces.each_key do |interface_name|

      # Here we are iterating over all interface addresses to find
      # inet address matched ipaddr method argument
      interfaces[interface_name][:addresses].each_key do |addr_name|
        if addr_name =~ /^#{ipaddr}$/ and 
            interfaces[interface_name][:addresses][addr_name][:family] =~ /^inet$/
          interface_addr = interfaces[interface_name][:addresses][addr_name]
          return {:name => interface_name, :addr => addr_name, :addropts => interface_addr}
        end
      end
    end
    return nil
  end


  def self.default_conf(chefnode)
    found = find_by_ip(chefnode[:ipaddress], chefnode)
    ip = IPAddr.new(found[:addr]).mask(found[:addropts][:netmask])

    netsize = ip.to_range.to_a.size
    dhcp_range = "#{ip.to_range.to_a[netsize - 2 - netsize/2]},#{ip.to_range.to_a[netsize - 2]}"
    
    return {
      :server => found[:addr],
      :gateway => found[:addr],
      :next_server => found[:addr],
      :dhcp_range => dhcp_range 
    }
  end

end
