require 'json'
require 'timeout'

PUPPET_TIMEOUT = 60*60

module Astute
  class DeploymentEngine
    def initialize(context)
      @ctx = context
      @pattern_spec = {'type' => 'count-lines',
        'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
        'expected_line_number' => 500}
      @deployLogParser = Astute::LogParser::ParseNodeLogs.new('puppet-agent.log', @pattern_spec)
    end

    def deploy(nodes, attrs)
      # FIXME(mihgen): hardcode simple_compute for now
      attrs['deployment_mode'] ||= 'simple_compute'
      Astute.logger.info "Deployment mode #{attrs['deployment_mode']}, using #{self.class} for deployment."
      result = self.send("deploy_#{attrs['deployment_mode']}", nodes, attrs)
    end

    def method_missing(method, *args)
      Astute.logger.error "Method #{method} is not implemented for #{self.class}"
    end

    # This method is called by Ruby metaprogramming magic from deploy method
    # It should not contain any magic with attributes, and should not directly run any type of MC plugins
    # It does only support of deployment sequence. See deploy_piece implementation in subclasses.
    def deploy_simple_compute(nodes, attrs)
      ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
      attrs = extend_attrs(nodes, attrs)
      Astute.logger.info "Starting deployment of controllers"
      deploy_piece(ctrl_nodes, attrs)

      @deployLogParser.pattern_spec['expected_line_number'] = 380
      compute_nodes = nodes.select {|n| n['role'] == 'compute'}
      Astute.logger.info "Starting deployment of computes"
      deploy_piece(compute_nodes, attrs)

      @deployLogParser.pattern_spec['expected_line_number'] = 300
      other_nodes = nodes - ctrl_nodes - compute_nodes
      Astute.logger.info "Starting deployment of other nodes"
      deploy_piece(other_nodes, attrs)
      return
    end

    private
    def nodes_status(nodes, status)
      {'nodes' => nodes.map { |n| {'uid' => n['uid'], 'status' => status} }}
    end

    def extend_attrs(nodes, attrs)
      # See overrides in subclasses
      attrs
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
  
