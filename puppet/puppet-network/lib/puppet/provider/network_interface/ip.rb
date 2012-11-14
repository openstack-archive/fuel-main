Puppet::Type.type(:network_interface).provide(:ip) do

  # ip command is preferred over ifconfig
  commands :ip => "/sbin/ip", :vconfig => "/sbin/vconfig"

  # Uses the ip command to determine if the device exists
  def exists?
#    ip('link', 'list', @resource[:name])
    ip('addr', 'show', 'label', @resource[:device]).include?("inet")
  rescue Puppet::ExecutionFailure
    return false
#     raise Puppet::Error, "Network interface %s does not exist" % @resource[:name] 
  end 

  def create
    if @resource[:vlan] == :yes && ! ip('link', 'list').include?(@resource[:name].split(':').first)
      # Create vlan device
      vconfig('add', @resource[:device].split('.').first, @resource[:device].split('.').last)
    end
    unless self.netmask == @resource.should(:netmask) || self.broadcast == @resource.should(:broadcast) || self.ipaddr == @resource.should(:ipaddr)
      ip_addr_flush
      ip_addr_add
    end
    unless self.state == @resource.should(:state)
      self.state=(@resource.should(:state))
    end
  end

  def destroy
    ip_addr_flush
    if @resource[:vlan] == :yes
      # Test if no ip addresses are configured on this vlan device
      if ! ip('addr', 'show', @resource[:device].split(':').first).include?("inet")
        # Destroy vlan device
        vconfig('rem', @resource[:device].split(':').first)
      end
    end
  end


 # NETMASK
  def netmask
    lines = ip('addr', 'show', 'label', @resource[:device])
    lines.scan(/\s*inet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)\/(\d+) b?r?d?\s*(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)?\s*scope (\w+) (\w+:?\d*)/)
    $2.nil? ? :absent : $2
  end

  def netmask=(value)
    ip_addr_flush
    ip_addr_add
  end

 # BROADCAST
  def broadcast
    lines = ip('addr', 'show', 'label', @resource[:device])
    lines.scan(/\s*inet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)\/(\d+) b?r?d?\s*(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)?\s*scope (\w+) (\w+:?\d*)/)
    $3.nil? ? :absent : $3
  end

  def broadcast=(value)
    ip_addr_flush
    ip_addr_add
  end

 # IPADDR
  def ipaddr
    lines = ip('addr', 'show', 'label', @resource[:device])
    lines.scan(/\s*inet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)\/(\d+) b?r?d?\s*(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)?\s*scope (\w+) (\w+:?\d*)/)
    $1.nil? ? :absent : $1
  end

  def ipaddr=(value)
    ip_addr_flush
    ip_addr_add
  end

  
  def ip_addr_flush
    ip('addr', 'flush', 'dev', @resource[:device], 'label', @resource[:device].sub(/:/, '\:'))
  end

  def ip_addr_add
    ip('addr', 'add', @resource[:ipaddr] + "/" + @resource[:netmask], 'broadcast', @resource[:broadcast], 'label', @resource[:device], 'dev', @resource[:device])
  end

  def device
    config_values[:dev]
  end
  
  # Ensurable/ensure adds unnecessary complexity to this provider
  # Network interfaces are up or down, present/absent are unnecessary
  def state
    lines = ip('link', 'list', @resource[:name])
    if lines.include?("UP")
      return "up"
    else
      return "down"
    end 
  end

  # Set the interface's state
  # FIXME Facter bug #2211 prevents puppet from bringing up network devices
  def state=(value)
    ip('link', 'set', @resource[:name], value)
  end

  # Current state of the device via the ip command
  def state_values
    @values ||= read_ip_output
  end

  # Return the ip output of the device
  def ip_output
    ip('addr','show', 'dev', @resource[:name])
  end

  # FIXME Back Named Reference Captures are supported in Ruby 1.9.x
  def read_ip_output
    output = ip_output
    lines = output.split("\n")
    line1 = lines.shift
    line2 = lines.shift
    i=0
    j=0
    p=0
   
    # Append ipv6 lines into one string
    lines.each do |line|
      if line.include?("inet6")
        lines[p] = lines[p] + lines[p+1]
        lines.delete_at(p+1)
      else
        # move along, nothing to see here
      end
       p += 1 
    end

    #FIXME This should capture 'NOARP' and 'MULTICAST'
    # Scan the first line of the ip command output
    line1.scan(/\d: (\w+): <(\w+),(\w+),(\w+),?(\w*)> mtu (\d+) qdisc (\w+) state (\w+)\s*\w* (\d+)*/)
    values = {  
      "device"    => $1,
      "mtu"       => $6,
      "qdisc"     => $7,
      "state"     => $8,
      "qlen"      => $9, 
    }
    
    # Scan the second line of the ip command output
    line2.scan(/\s*link\/\w+ ((?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}) brd ((?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2})/) 
    values["address"]   = $1
    values["broadcast"] = $2 
   
    # Scan all the inet and inet6 entries
    lines.each do |line|
      if line.include?("inet6") 
        line.scan(/\s*inet6 ((?>[0-9,a-f,A-F]*\:{1,2})+[0-9,a-f,A-F]{0,4})\/\w+ scope (\w+)\s*\w*\s*valid_lft (\w+) preferred_lft (\w+)/)
        values["inet6_#{j}"] = { 
          "ip"              => $1,
          "scope"           => $2, 
          "valid_lft"       => $3,
          "preferred_lft"   => $4, 
        }
        j += 1
      else
        line.scan(/\s*inet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)\/\d+ b?r?d?\s*(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)?\s*scope (\w+) (\w+:?\d*)/)
        values["inet_#{i}"] = { 
          "ip"         => $1,
          "brd"        => $2,
          "scope"      => $3,
          "dev"        => $4, 
        }
        i += 1
      end
    end
    
  return values

  end

  #FIXME Need to support multiple inet & inet6 hashes
  IP_ARGS = [ "qlen", "mtu", "address" ]

  IP_ARGS.each do |ip_arg|
    define_method(ip_arg.to_s.downcase) do
      state_values[ip_arg]
    end
    
    define_method("#{ip_arg}=".downcase) do |value|
      ip('link', 'set', "#{ip_arg}", value, 'dev', @resource[:name])
      state_values[ip_arg] = value
    end
  end
  
end
