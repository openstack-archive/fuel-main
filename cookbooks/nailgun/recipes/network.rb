
for network_name, network_params in (node['networks'] || {})

  network_interface network_params['device'] do
    vlan network_params['vlan_id']
    address network_params['address']
    netmask network_params['netmask']
  end

end

