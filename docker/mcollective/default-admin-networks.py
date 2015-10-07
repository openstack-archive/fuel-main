#!/usr/bin/python

import yaml

with open('/etc/hiera/astute.yaml') as f:
    astute_data = yaml.load(f)

admin_network = astute_data['ADMIN_NETWORK']
networks_data = {
    'admin_networks':
        [{
            'id': '1',
            'node_group_name': 'default',
            'node_group_id': '1',
            'cluster_name': 'default',
            'cluster_id': '1',
            'cidr': admin_network['cidr'],
            'gateway': admin_network['dhcp_gateway'],
            'ip_ranges': [[
                admin_network['dhcp_pool_start'],
                admin_network['dhcp_pool_end']
            ]]
        },]
}

with open('/etc/hiera/networks.yaml', 'w') as f:
    f.write(yaml.dump(networks_data, default_style='"'))

