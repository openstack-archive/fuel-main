require 'json'
require 'ipaddr'

module Astute
  module Metadata
    def self.publish_facts(ctx, nodes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to post metadata into are not provided. Do nothing."
        return false
      end
      uids = nodes.map {|n| n['uid']}
      Astute.logger.debug "#{ctx.task_id}: nailyfact - storing metadata for nodes: #{uids.join(',')}"

      nodes.each do |node|
        nailyfact = MClient.new(ctx, "nailyfact", [node['uid']])
        intfhash = Hash.new do |hash, key|
            hash[key] = {}
        end
        node['network_data'].each do |intf|
            if intf['vlan'].size>0
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
	metadata = {'role' => node['role'], 'id' => node['id'], 'uid' => node['uid'], 'network_data' => intfhash.to_json }

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = nailyfact.post(:value => metadata.to_json)
      end
    end
  end
end
