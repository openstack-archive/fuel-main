# Network cookbook

## Resources

* network_interface - configure network interface

    network_interface 'eth0' do
      address '192.168.1.2'
      netmask '255.255.255.0'
    end

  or

    # configure VLAN interface with automatic address via DHCP
    network_interface 'eth0.50'

  Attributes:

  * address - IPv4 network interface address
  * netmask - network mask in IPv4 format (e.g. '255.255.255.0')
  * vlan    - vlan ID
  * mtu     - interface's MTU value
  * metric  - interface's metric value
  * onboot  - start this interface on boot (defaults to true)


