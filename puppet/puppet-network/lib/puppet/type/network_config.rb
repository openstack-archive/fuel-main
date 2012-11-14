require 'puppet'

module Puppet

  Puppet::Type.newtype(:network_config) do
    @doc = "The network configuration type"

    ensurable

    newparam(:exclusive) do
      d = "Enforces that no network configuration exists besides what puppet defines.\n"
      d << "Enabled by default, set it to false in any resource to disable globally."
      desc(d)

      newvalues(:true, :false)
      # this behaviorally defaults to true (see network_scripts.rb exists?()/initialize())
      # using defaultto(:true) would prevent users from setting this to false
    end

    newparam(:device) do
      isnamevar
      desc "The network device to be configured"
    end

    newparam(:bootproto) do
      desc "Boot priority for the network device"
      newvalues(:dhcp, :static, :none)
      defaultto(:dhcp)
    end

    newparam(:onboot) do
      desc "Start the network device on boot"
      newvalues(:yes, :no)
      defaultto(:yes)
    end

    newparam(:nozeroconf) do
      desc "Skip zeroconf (aka local-link) configuration"
      newvalues(:yes, :no)
    end

    newparam(:netmask) do
      desc "Configure the subnetmask of the device"
    end

    newparam(:prefix) do
      desc "Configure the network prefix, Has precedence over NETMASK on redhat."
    end

    newparam(:network) do
      desc "Configure the network of the device"
    end

    newparam(:broadcast) do
      desc "Configure the broadcast of the device"
    end

    newparam(:ipaddr) do
      desc "Configure the IP address of the device"
    end

    newparam(:gateway) do
      desc "Configure the Gateway of the device"
    end

    newparam(:hwaddr) do
      desc "Hardware address of the device"
    end

    newparam(:domain) do
      desc "Configure the domain of the device"
    end

    newparam(:bridge) do
      desc "The bridge in which the device is enslaved (if any)"
    end

    newparam(:stp) do
      desc "Enable STP (only applicable to type=Bridge devices)"
    end

    newparam(:delay) do
      desc "Configure forward delay (only applicable to type=Bridge devices)"
    end

    newparam(:peerdns) do
      desc "modify /etc/resolv.conf if peer uses msdns extension (PPP only) or
 DNS{1,2} are set, or if using dhclient. default to 'yes'."
      newvalues(:yes, :no)
    end

    newparam(:dns1) do
      desc "primary DNS server IPADDR"
    end

    newparam(:dns2) do
      desc "secondary DNS server IPADDR"
    end

    newparam(:type) do
      desc "Type of the device"
      newvalues(:Ethernet, :Bridge, :Bonding)
    end

    newparam(:vlan) do
      desc "Is the device VLAN tagged (802.1q)"
      newvalues(:yes, :no)
    end

    newparam(:userctl) do
      desc "Non root users are allowed to control device if set to yes"
      newvalues(:yes, :no)
      defaultto(:no)
    end

    newparam(:bonding_opts) do
      desc "Configures bonding parameter"
    end

    newparam(:master) do
      desc "Configures the bonding device to which the device is enslaved (set 'slave=>yes' too)"
    end

    newparam(:slave) do
      desc "Configures whether or not the device is enslaved to a bonding device"
      newvalues(:yes, :no)
    end
  end
end
