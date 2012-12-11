require 'json'
require 'timeout'

PUPPET_TIMEOUT = 60*60

module Astute
  module Deployer
    private
    def self.calculate_networks(data)
      interfaces = {}
      data.each do |iface|
        if iface['vlan'] and iface['vlan'] != 0
          name = [iface['dev'], iface['vlan']].join('.')
          interfaces[name] = {"vlan" => "yes"}
        else
          name = iface['dev']
        end
        interfaces[name]['bootproto'] = 'none'
        if iface['ip']
          ipaddr = iface['ip'].split('/')[0]
          interfaces[name]['ipaddr'] = ipaddr
          interfaces[name]['netmask'] = iface['netmask']  #=IPAddr.new('255.255.255.255').mask(ipmask[1]).to_s
          interfaces[name]['bootproto'] = 'static'
          if iface['brd']
            interfaces[name]['broadcast'] = iface['brd']
          end
        end
        interfaces[name]['ensure'] = 'present'
      end
      interfaces['lo'] = {} unless interfaces.has_key?('lo')
      interfaces['eth0'] = {'bootproto' => 'dhcp',
                            'ensure' => 'present'} unless interfaces.has_key?('eth0')
      # Example of return:
      # {"eth0":{"ensure":"present","bootproto":"dhcp"},"lo":{},
      # "eth0.102":{"ipaddr":"10.20.20.20","ensure":"present","vlan":"yes",
      #     "netmask":"255.255.255.0","broadcast":"10.20.20.255","bootproto":"static"}}
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

      Astute.logger.info "#{ctx.task_id}: Calculation of required attributes to pass, include netw.settings"
      nodes.each do |node|
        network_data = calculate_networks(node['network_data'])
        metadata = {'role' => node['role'], 'uid' => node['uid'], 'network_data' => network_data.to_json }
        attrs.each do |k, v|
          metadata[k] = v  # TODO(mihgen): needs to be much smarter than this. This will work only with simple string.
        end
        # Let's calculate interface settings we need for OpenStack:
        node['network_data'].each do |iface|
          device = (iface['vlan'] and iface['vlan'] > 0) ? [iface['dev'], iface['vlan']].join('.') : iface['dev']
          metadata[iface['name'] + '_interface'] = device
        end

        metapublisher.call(ctx, node['uid'], metadata)
      end
      Astute.logger.info "#{ctx.task_id}: All required attrs/metadata passed via facts extension. Starting deployment."
      Astute::PuppetdDeployer.deploy(ctx, nodes)
    end

    def self.rpuppet_deploy(ctx, nodes, attrs)
      classes = {"nailytest::test_rpuppet" => {"rpuppet" => ["controller", "privet"]}}
      Astute::RpuppetDeployer.rpuppet_deploy(ctx, nodes, attrs, classes)
    end
  end
end
  
