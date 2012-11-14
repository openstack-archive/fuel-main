require 'puppet'
require 'mocha'
require '/etc/puppet/modules/puppet-network/lib/puppet/provider/network_config/network_scripts.rb'

provider_class = Puppet::Type.type(:network_config).provider(:network_scripts)

describe provider_class do
  before do
    @provider = provider_class.new 
  end
  it "should read config file" do
    File.stubs(:exist?).returns true 
    filemock = stub "Network File"
    File.stubs(:new).returns filemock
    filemock.stubs(:readlines).returns [
      "#this is a comment",
      "USRCTL=no",
      "IPADDR=127.0.0.1",
      "BOOTPROTO=dhcp\n",
      "ONBOOT=yes",
    ]
 
    @provider.read_config.should == {
      :USRCTL => "no",
      :IPADDR => "127.0.0.1",
      :BOOTPROTO => "dhcp",
      :ONBOOT => "yes",
    }

  end
   
end
