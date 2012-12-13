class Astute::DeploymentEngine::NailyFact < Astute::DeploymentEngine

  # This is the main method where we mix all attrs and prepare them for Puppet
  # It's called from superclass's main deployment method
  def extend_attrs(nodes, attrs)
    ctrl_nodes = nodes.select {|n| n['role'] == 'controller'}
    # TODO(mihgen): we should report error back if there are not enough metadata passed
    ctrl_management_ips = []
    ctrl_public_ips = []
    ctrl_nodes.each do |n|
      ctrl_management_ips << n['network_data'].select {|nd| nd['name'] == 'management'}[0]['ip']
      ctrl_public_ips << n['network_data'].select {|nd| nd['name'] == 'public'}[0]['ip']
    end

    # TODO(mihgen): we take first IP, is it Ok for all installations? I suppose it would not be for HA..
    attrs['controller_node_address'] = ctrl_management_ips[0].split('/')[0]
    attrs['controller_node_public'] = ctrl_public_ips[0].split('/')[0]
    attrs
  end

  def create_facts(node, attrs)
    metapublisher = Astute::Metadata.method(:publish_facts)
    # calculate_networks method is common and you can find it in superclass
    # if node['network_data'] is undefined, we use empty list because we later try to iterate over it
    #   otherwise we will get KeyError
    node_network_data = node['network_data'] or []
    network_data_puppet = calculate_networks(node_network_data)
    metadata = {'role' => node['role'], 'uid' => node['uid'], 'network_data' => network_data_puppet.to_json }
    attrs.each do |k, v|
      metadata[k] = v  # TODO(mihgen): needs to be much smarter than this. This will work only with simple string.
    end
    # Let's calculate interface settings we need for OpenStack:
    node_network_data.each do |iface|
      device = (iface['vlan'] and iface['vlan'] > 0) ? [iface['dev'], iface['vlan']].join('.') : iface['dev']
      metadata[iface['name'] + '_interface'] = device
    end

    metapublisher.call(@ctx, node['uid'], metadata)
  end

  def deploy_piece(nodes, attrs)
    return false unless validate_nodes(nodes)
    @ctx.reporter.report nodes_status(nodes, 'deploying')

    Astute.logger.info "#{@ctx.task_id}: Calculation of required attributes to pass, include netw.settings"
    nodes.each do |node|
      create_facts(node, attrs)
    end
    Astute.logger.info "#{@ctx.task_id}: All required attrs/metadata passed via facts extension. Starting deployment."

    Astute::PuppetdDeployer.deploy(@ctx, nodes)
    @ctx.reporter.report nodes_status(nodes, 'ready')
    nodes_roles = nodes.map { |n| { n['uid'] => n['role'] } }
    Astute.logger.info "#{@ctx.task_id}: Finished deployment of nodes => roles: #{nodes_roles.inspect}"
  end
end
