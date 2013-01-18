require 'json'
require 'timeout'

PUPPET_TIMEOUT = 60*60
PUPPET_FADE_TIMEOUT = 60

module Astute
  class DeploymentEngine
    def initialize(context)
      @ctx = context
      @pattern_spec = {'type' => 'count-lines',
        'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
        'expected_line_number' => 500}
      @deploy_log_parser = Astute::LogParser::ParseNodeLogs.new('puppet-agent.log', @pattern_spec)
    end

    def deploy(nodes, attrs)
      attrs['deployment_mode'] ||= 'multinode_compute'  # simple multinode deployment is the default
      nodes.each {|n| n['uid'] = n['uid'].to_s }  # It may fail if uid is Fixnum
      Astute.logger.info "Deployment mode #{attrs['deployment_mode']}, using #{self.class} for deployment."
      attrs_for_mode = self.send("attrs_#{attrs['deployment_mode']}", nodes, attrs)
      result = self.send("deploy_#{attrs['deployment_mode']}", nodes, attrs_for_mode)
    end

    def method_missing(method, *args)
      Astute.logger.error "Method #{method} is not implemented for #{self.class}, raising exception."
      raise "Method #{method} is not implemented for #{self.class}"
    end

    def attrs_singlenode_compute(nodes, attrs)
      ctrl_management_ip = nodes[0]['network_data'].select {|nd| nd['name'] == 'management'}[0]['ip']
      ctrl_public_ip = nodes[0]['network_data'].select {|nd| nd['name'] == 'public'}[0]['ip']
      attrs['controller_node_address'] = ctrl_management_ip.split('/')[0]
      attrs['controller_node_public'] = ctrl_public_ip.split('/')[0]
      attrs
    end

    def deploy_singlenode_compute(nodes, attrs)
      # TODO(mihgen) some real stuff is needed
      Astute.logger.info "Starting deployment of single node OpenStack"
      deploy_piece(nodes, attrs)
    end

    # we mix all attrs and prepare them for Puppet
    # Works for multinode_compute deployment mode
    def attrs_multinode_compute(nodes, attrs)
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
    def deploy_multinode_compute(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      Astute.logger.info "Starting deployment of controllers"
      deploy_piece(ctrl_nodes, attrs)

      @deploy_log_parser.pattern_spec['expected_line_number'] = 380
      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      @deploy_log_parser.pattern_spec['expected_line_number'] = 300
      other_nodes = nodes - ctrl_nodes - compute_nodes
      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    def attrs_ha_compute(nodes, attrs)
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

    def deploy_ha_compute(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      Astute.logger.info "Starting deployment of 1st controller, ignoring failure"
      deploy_piece([ctrl_nodes[0]], attrs, retries=0, ignore_failure=true)

      except_first_ctrls = ctrl_nodes.clone
      except_first_ctrls.delete_at(0)
      Astute.logger.info "Starting deployment of controllers: #{except_first_ctrls.map{|x| x['uid']}},"\
                         " ignoring failure"
      deploy_piece(except_first_ctrls, attrs, retries=0, ignore_failure=true)

      Astute.logger.info "Starting deployment of all controllers, ignoring failure"
      deploy_piece(ctrl_nodes, attrs, retries=0, ignore_failure=true)

      Astute.logger.info "Starting deployment of 1st controller again, ignoring failure"
      deploy_piece([ctrl_nodes[0]], attrs, retries=0, ignore_failure=true)

      retries = 1
      Astute.logger.info "Starting deployment of all controllers until it completes, "\
                         "allowed retries: #{retries}"
      deploy_piece(ctrl_nodes, attrs, retries=retries)

      # FIXME(mihgen): put right numbers for logs
      @deploy_log_parser.pattern_spec['expected_line_number'] = 380
      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      @deploy_log_parser.pattern_spec['expected_line_number'] = 300
      other_nodes = nodes - ctrl_nodes - compute_nodes
      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    private
    def nodes_status(nodes, status)
      {'nodes' => nodes.map { |n| {'uid' => n['uid'], 'status' => status} }}
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
  
