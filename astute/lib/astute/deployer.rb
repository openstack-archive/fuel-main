require 'json'
require 'timeout'

PUPPET_TIMEOUT = 30*60

module Astute
  module Deployer
    private
    def self.calculate_networks(data)
      # {"eth0":{"ensure":"present","bootproto":"dhcp"},"lo":{},
      # "eth0.102":{"ipaddr":"10.20.20.20","ensure":"present","vlan":"yes",
      #     "netmask":"255.255.255.0","broadcast":"10.20.20.255","bootproto":"static"}}

      interfaces = {}
      data.each do |iface|
        if iface['vlan'] and iface['vlan'] != 0
          name = [iface['dev'], iface['vlan']].join('.')
          interfaces[name] = {"vlan" => "yes"}
        else
          name = iface['dev']
        end
        if iface['ip']
          ipaddr = iface['ip'].split('/')[0]
          interfaces[name]['ipaddr'] = ipaddr
          interfaces[name]['netmask'] = iface['netmask']  #=IPAddr.new('255.255.255.255').mask(ipmask[1]).to_s
          interfaces[name]['bootproto']="static"
        end
        interfaces[name]['ensure']="present"
      end
      interfaces['lo'] = {} unless interfaces.has_key?('lo')
      interfaces['eth0'] = {'bootproto' => 'dhcp',
                            'ensure' => 'present'} unless interfaces.has_key?('eth0')
      return interfaces
    end

    public
    def self.puppet_deploy_with_polling(ctx, nodes, attrs)
      # Preparing parameters here
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to deploy are not provided. Do nothing."
        return false
      end
      metapublisher = Astute::Metadata.method(:publish_facts)

      nodes.each do |node|
        network_data = calculate_networks(node['network_data'])
        metadata = {'role' => node['role'], 'uid' => node['uid'], 'network_data' => network_data.to_json }
        attrs.each do |k, v|
          metadata[k] = v.to_json
        end

        metapublisher.call(ctx, node['uid'], metadata)
      end

      Astute::PuppetdDeployer.deploy(ctx, nodes)
    end

    def self.rpuppet_deploy(ctx, nodes, attrs)
      classes = {"nailytest::test_rpuppet" => {"rpuppet" => ["controller", "privet"]}}
      Astute::RpuppetDeployer.rpuppet_deploy(ctx, nodes, attrs, classes)
    end
  end
end
  
