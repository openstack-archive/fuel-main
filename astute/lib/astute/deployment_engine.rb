require 'json'
require 'timeout'

module Astute
  class DeploymentEngine
    def initialize(context)
      if self.class.superclass.name == 'Object'
        raise "Instantiation of this superclass is not allowed. Please subclass from #{self.class.name}."
      end
      @ctx = context
    end

    def deploy(nodes, attrs)
      # See implementation in subclasses, this may be everriden
      attrs['deployment_mode'] ||= 'multinode'  # simple multinode deployment is the default
      attrs['use_cinder'] ||= nodes.any?{|n| n['role'] == 'cinder'}
      @ctx.deploy_log_parser.deploy_type = attrs['deployment_mode']
      Astute.logger.info "Deployment mode #{attrs['deployment_mode']}"
      result = self.send("deploy_#{attrs['deployment_mode']}", nodes, attrs)
    end

    def method_missing(method, *args)
      Astute.logger.error "Method #{method} is not implemented for #{self.class}, raising exception."
      raise "Method #{method} is not implemented for #{self.class}"
    end

    def attrs_singlenode(nodes, attrs)
      ctrl_management_ip = nodes[0]['network_data'].select {|nd| nd['name'] == 'management'}[0]['ip']
      ctrl_public_ip = nodes[0]['network_data'].select {|nd| nd['name'] == 'public'}[0]['ip']
      attrs['controller_node_address'] = ctrl_management_ip.split('/')[0]
      attrs['controller_node_public'] = ctrl_public_ip.split('/')[0]
      attrs
    end

    def deploy_singlenode(nodes, attrs)
      # TODO(mihgen) some real stuff is needed
      Astute.logger.info "Starting deployment of single node OpenStack"
      deploy_piece(nodes, attrs)
    end

    # we mix all attrs and prepare them for Puppet
    # Works for multinode deployment mode
    def attrs_multinode(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      # TODO(mihgen): we should report error back if there are not enough metadata passed
      ctrl_management_ips = []
      ctrl_public_ips = []
      ctrl_nodes.each do |n|
        ctrl_management_ips << n['network_data'].select {|nd| nd['name'] == 'management'}[0]['ip']
        ctrl_public_ips << n['network_data'].select {|nd| nd['name'] == 'public'}[0]['ip']
      end

      attrs['controller_node_address'] = ctrl_management_ips[0].split('/')[0]
      attrs['controller_node_public'] = ctrl_public_ips[0].split('/')[0]
      attrs
    end

    # This method is called by Ruby metaprogramming magic from deploy method
    # It should not contain any magic with attributes, and should not directly run any type of MC plugins
    # It does only support of deployment sequence. See deploy_piece implementation in subclasses.
    def deploy_multinode(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      Astute.logger.info "Starting deployment of controllers"
      deploy_piece(ctrl_nodes, attrs)

      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      other_nodes = nodes - ctrl_nodes - compute_nodes
      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    def attrs_ha(nodes, attrs)
      # TODO(mihgen): we should report error back if there are not enough metadata passed
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      ctrl_manag_addrs = {}
      ctrl_public_addrs = {}
      ctrl_nodes.each do |n|
        # current puppet modules require `hostname -s`
        hostname = n['fqdn'].split(/\./)[0]
        ctrl_manag_addrs.merge!({hostname =>
                   n['network_data'].select {|nd| nd['name'] == 'management'}[0]['ip'].split(/\//)[0]})
        ctrl_public_addrs.merge!({hostname =>
                   n['network_data'].select {|nd| nd['name'] == 'public'}[0]['ip'].split(/\//)[0]})
      end

      attrs['ctrl_hostnames'] = ctrl_nodes.map {|n| n['fqdn'].split(/\./)[0]}
      attrs['master_hostname'] = ctrl_nodes[0]['fqdn'].split(/\./)[0]
      attrs['ctrl_public_addresses'] = ctrl_public_addrs
      attrs['ctrl_management_addresses'] = ctrl_manag_addrs
      attrs
    end

    def deploy_ha(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      Astute.logger.info "Starting deployment of all controllers one by one, ignoring failure"
      ctrl_nodes.each {|n| deploy_piece([n], attrs, retries=0, change_node_status=false)}

      Astute.logger.info "Starting deployment of all controllers, ignoring failure"
      deploy_piece(ctrl_nodes, attrs, retries=0, change_node_status=false)

      Astute.logger.info "Starting deployment of 1st controller again, ignoring failure"
      deploy_piece([ctrl_nodes[0]], attrs, retries=0, change_node_status=false)

      Astute.logger.info "Starting deployment of all controllers, retries=0"
      deploy_piece(ctrl_nodes, attrs, retries=0, change_node_status=false)
      retries = 3
      Astute.logger.info "Starting deployment of all controllers until it completes, "\
                         "allowed retries: #{retries}"
      deploy_piece(ctrl_nodes, attrs, retries=retries)

      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      other_nodes = nodes - ctrl_nodes - compute_nodes
      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    def deploy_ha_compact(nodes, attrs)
      # Added for backward compatibility with FUEL.
      # Should be used with `simplepuppet' engine only.
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      other_nodes = nodes - ctrl_nodes - compute_nodes

      Astute.logger.info "Starting deployment of all controllers one by one, ignoring failure"
      ctrl_nodes.each {|n| deploy_piece([n], attrs, retries=0, change_node_status=false)}

      Astute.logger.info "Starting deployment of 1st controller again, ignoring failure"
      deploy_piece(ctrl_nodes[0..0], attrs, retries=0, change_node_status=false)

      Astute.logger.info "Starting deployment of controllers exclude first, ignoring failure"
      deploy_piece(ctrl_nodes[1..-1], attrs, retries=0, change_node_status=false)

      Astute.logger.info "Starting deployment of 1st controller again"
      deploy_piece(ctrl_nodes[0..0], attrs, retries=0)

      Astute.logger.info "Starting deployment of controllers exclude first"
      deploy_piece(ctrl_nodes[1..-1], attrs, retries=0)

      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)

      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)
      return
    end

    def deploy_ha_full(nodes, attrs)
      # Added for backward compatibility with FUEL.
      # Should be used with `simplepuppet' engine only.
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      quantum_nodes = nodes.select {|n| n['role'] == 'quantum'}
      storage_nodes = nodes.select {|n| n['role'] == 'storage'}
      proxy_nodes = nodes.select {|n| n['role'] == 'swift-proxy'}
      other_nodes = nodes - ctrl_nodes - compute_nodes - quantum_nodes - storage_nodes -proxy_nodes

      Astute.logger.info "Starting deployment of all controllers one by one"
      ctrl_nodes.each {|n| deploy_piece([n], attrs, retries=0)}

      Astute.logger.info "Starting deployment of 1st controller again"
      deploy_piece(ctrl_nodes[0..0], attrs, retries=0)

      unless quantum_nodes.empty?
        Astute.logger.info "Starting deployment of Quantum nodes"
        deploy_piece(quantum_nodes, attrs, retries=0)
      end

      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      Astute.logger.info "Starting deployment of storages, ignoring failure"
      deploy_piece(storage_nodes, attrs, 2, change_node_status=false)

      Astute.logger.info "Starting deployment of storages, ignoring failure"
      deploy_piece(storage_nodes, attrs, 2, change_node_status=false)

      Astute.logger.info "Starting deployment of all proxies one by one, ignoring failure"
      proxy_nodes.each {|n| deploy_piece([n], attrs, retries=0, change_node_status=false)}

      Astute.logger.info "Starting deployment of storages"
      deploy_piece(storage_nodes, attrs)

      Astute.logger.info "Starting deployment of proxies"
      deploy_piece(proxy_nodes, attrs)

      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    private
    def nodes_status(nodes, status, data_to_merge)
      {'nodes' => nodes.map { |n| {'uid' => n['uid'], 'status' => status}.merge(data_to_merge) }}
    end

    def validate_nodes(nodes)
      if nodes.empty?
        Astute.logger.info "#{@ctx.task_id}: Nodes to deploy are not provided. Do nothing."
        return false
      end
      return true
    end

    def calculate_networks(data)
      interfaces = {}
      data ||= []
      Astute.logger.info "calculate_networks function was provided with #{data.size} interfaces"
      data.each do |iface|
        Astute.logger.debug "Calculating network for #{iface.inspect}"
        if iface['vlan'] and iface['vlan'] != 0
          name = [iface['dev'], iface['vlan']].join('.')
          interfaces[name] = {"vlan" => "yes"}
        else
          name = iface['dev']
          interfaces[name] = {}
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
        if iface['gateway'] and iface['name'] =~ /^public$/i
          interfaces[name]['gateway'] = iface['gateway']
        end
        interfaces[name]['ensure'] = 'present'
        Astute.logger.debug "Calculated network for interface: #{name}, data: #{interfaces[name].inspect}"
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
  end
end

