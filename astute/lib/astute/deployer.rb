require 'json'
require 'timeout'

PUPPET_TIMEOUT = 30*60

module Astute
  module Deployer
    private
    def self.calculate_networks(data)
      # TODO(mihgen): refactor this
      intfhash = Hash.new do |hash, key|
        hash[key] = {}
      end
      data.each do |intf|
        if intf['vlan'].size > 0
          name="#{intf['dev']}.#{intf['vlan']}"
          intfhash[name]={"vlan"=>"yes"}
        else
          name=intf['dev']
        end
        if intf['ip'].size>0
          ipmask=intf['ip'].split('/')
          intfhash[name]['ipaddr']=ipmask[0]
          intfhash[name]['netmask']=IPAddr.new('255.255.255.255').mask(ipmask[1]).to_s
          intfhash[name]['bootproto']="static"
          if intf['brd'].size>0
            intfhash[name]['broadcast']=intf['brd']
          end
          intfhash[name]['ensure']="present"
        else
          intfhash[name]['bootproto']="dhcp"
        end
      end
      if ! intfhash.has_key?("lo")
        intfhash["lo"]={}
      end
      if ! intfhash.has_key?("eth0")
        intfhash["eth0"]={"bootproto"=>"dhcp","ensure"=>"present"}
      end
      return intfhash
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
        metadata.merge!(attrs.map {|k, v| k => v.to_json})

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
  
