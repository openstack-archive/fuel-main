require 'puppet'
require 'ruby-debug'
require 'mocha'
require 'lib/puppet/provider/network_interface/ip.rb'


provider_class = Puppet::Type.type(:network_interface).provider(:ip)

describe provider_class do

  before do
    @resource = stub("resource", :name => "lo")
    @resource.stubs(:[]).with(:name).returns "lo"
    @resource.stubs(:[]).returns "lo"
    @provider = provider_class.new(@resource) 
  end

  it "should parse ip link show output for loopback" do
    ip_output = <<-HEREDOC
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 16436 qdisc noqueue state UNKNOWN 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
HEREDOC

    @provider.stubs(:ip_output).returns(ip_output)
    hash = {  
      "device"      => "lo",
      #"dynamic"    => "on",
      #"multicast"  => "on",
      #"arp"        => "on",
      "mtu"         => "16436",
      "qdisc"       => "noqueue",
      "state"       => "UNKNOWN",
      "qlen"        => nil,
      "address"     => "00:00:00:00:00:00",
      "broadcast"   => "00:00:00:00:00:00",
      "inet_0" => {
        "ip"         => "127.0.0.1",
        "brd"        =>  nil,
        "scope"      => "host",
        "dev"        => "lo",
      },
      "inet6_0" => {
        "ip"            => "::1",
        "scope"         => "host",
        "valid_lft"     => "forever",
        "preferred_lft" => "forever",
      },
    }
    @provider.read_ip_output.should == hash
  end

  before do
    @resource = stub("resource", :name => "eth0")
    @resource.stubs(:[]).with(:name).returns "eth0"
    @resource.stubs(:[]).returns "eth0"
    @provider = provider_class.new(@resource) 
  end
  
  it "should parse ip addr show output with an ipv4" do
    ip_output = <<-HEREDOC
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
    link/ether 08:00:27:6c:c7:59 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.101/24 brd 192.168.56.255 scope global eth0
    inet6 fe80::a00:27ff:fe6c:c759/64 scope link 
       valid_lft forever preferred_lft forever
HEREDOC

    @provider.stubs(:ip_output).returns(ip_output)
      hash = {
        "device"      => "eth0",
        #"dynamic"    => "on",
        #"multicast"  => "on",
        #"arp"        => "on",
        "mtu"         => "1500",
        "qdisc"       => "pfifo_fast",
        "state"       => "UP",
        "qlen"        => "1000",
        "address"     => "08:00:27:6c:c7:59",
        "broadcast"   => "ff:ff:ff:ff:ff:ff",
        
        "inet_0" => {
          "ip"         => "192.168.56.101",
          "brd"        => "192.168.56.255",
          "scope"      => "global",
          "dev"        => "eth0",
        },
        "inet6_0" => {
          "ip"            => "fe80::a00:27ff:fe6c:c759",
          "scope"         => "link",
          "valid_lft"     => "forever",
          "preferred_lft" => "forever",
        }
      }
      @provider.read_ip_output.should == hash
    
  end
  
  it "should parse ip link show output with multiple ip addresses" do
    ip_output = <<-HEREDOC
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN qlen 1000
    link/ether 54:52:00:27:fd:71 brd ff:ff:ff:ff:ff:ff
    inet 131.252.208.54/24 brd 131.252.208.255 scope global eth0
    inet 131.252.208.79/32 brd 131.252.208.255 scope global eth0:2
    inet 131.252.208.98/32 brd 131.252.208.255 scope global eth0:3
    inet 131.252.208.61/32 brd 131.252.208.255 scope global eth0:12
    inet 131.252.208.66/32 brd 131.252.208.255 scope global eth0:13
    inet6 2610:10:20:208:5652:ff:fe27:fd71/64 scope global dynamic 
       valid_lft 2591858sec preferred_lft 604658sec
    inet6 2610:10:20:208::66/64 scope global 
       valid_lft forever preferred_lft forever
    inet6 2610:10:20:208::79/64 scope global 
       valid_lft forever preferred_lft forever
    inet6 fe80::5652:ff:fe27:fd71/64 scope link 
       valid_lft forever preferred_lft forever
HEREDOC
    @provider.stubs(:ip_output).returns(ip_output)
    hash = {  
      "device"      => "eth0",
      #"dynamic"    => "on",
      #"multicast"  => "on",
      #"arp"        => "on",
      "mtu"         => "1500",
      "qdisc"       => "pfifo_fast",
      "state"       => "UNKNOWN",
      "qlen"        => "1000",
      "address"     => "54:52:00:27:fd:71",
      "broadcast"   => "ff:ff:ff:ff:ff:ff",
      "inet_0" => {
        "ip"         => "131.252.208.54",
        "brd"        => "131.252.208.255",
        "scope"      => "global",
        "dev"        => "eth0",
      },
      "inet_1" => {
        "ip"         => "131.252.208.79",
        "brd"        => "131.252.208.255",
        "scope"      => "global",
        "dev"        => "eth0:2",
      },
      "inet_2" => {
        "ip"         => "131.252.208.98",
        "brd"        => "131.252.208.255",
        "scope"      => "global",
        "dev"        => "eth0:3",
      },
      "inet_3" => {
        "ip"         => "131.252.208.61",
        "brd"        => "131.252.208.255",
        "scope"      => "global",
        "dev"        => "eth0:12",
      },
      "inet_4" => {
        "ip"         => "131.252.208.66",
        "brd"        => "131.252.208.255",
        "scope"      => "global",
        "dev"        => "eth0:13",
      },
      "inet6_0" => {
        "ip"            => "2610:10:20:208:5652:ff:fe27:fd71",
        "scope"         => "global",
        "valid_lft"     => "2591858sec",
        "preferred_lft" => "604658sec"
      },
      "inet6_1" => {
        "ip"            => "2610:10:20:208::66",
        "scope"         => "global",
        "valid_lft"     => "forever",
        "preferred_lft" => "forever",
      },
      "inet6_2" => {
        "ip"            => "2610:10:20:208::79",
        "scope"         => "global",
        "valid_lft"     => "forever",
        "preferred_lft" => "forever",
      },
      "inet6_3" => {
        "ip"            => "fe80::5652:ff:fe27:fd71",
        "scope"         => "link",
        "valid_lft"     => "forever",
        "preferred_lft" => "forever",
      },
    }
    @provider.read_ip_output.should == hash
  end

end
