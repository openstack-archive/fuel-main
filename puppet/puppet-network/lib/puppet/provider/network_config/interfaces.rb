# This provider is in development and not ready for production

Puppet::Type.type(:network_config).provide(:interfaces) do

defaultfor :operatingsystem => [:ubuntu, :debian]
  # ... change this for interfaces 
  # iface eth0-@map_value
  #   key value
  #   address 192.168.1.1
  #   netmask 255.255.255.0
  #
  #   lines beginning with the work "auto" ~ onboot => yes
  # record_line :parsed, :fields => %w{address netmask gateway broadcast family method},
end
