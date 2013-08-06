Network Issues
==============

.. contents:: :local:

FuelWeb has built-in capability to run network check before or after OpenStack deployment. Currently it can check
connectivity between nodes within configured VLANs on configured server interfaces. Image below shows sample
result of such check. By using this simple table it is easy to say which interfaces do not receive certain VLAN IDs.
Usually it measn that switch or multiple switches are not configured correctly and do not allow certain tagged
traffic to pass through.

.. image:: _static/net_verify_failure.png

On VirtualBox
-------------

Scripts which are provided for quick FuelWeb setup, create 3 host-interface adapters. Basically
networking works as this being a 3 bridges, in each of them the only one VMs interfaces is connected.
It means there is only L2 connectivity between VMs on interfaces named by the same name.
If you try to move, for example, management network to eth1 on controller node, and the same network
to eth2 on the compute, then there will be no connectivity between OpenStack services in spite of being
configured to live on the same VLAN.
It easy to validate settings before deploy by clicking on "Verify Networks" button before deployment.

Timeout in connection to OpenStack API from client applications
---------------------------------------------------------------

If you use Java, Python or any other code to work with OpenStack API, all connections should be done over OpenStack public network.
To explain why we can not use FuelWeb admin network, let's try to run nova client with debug option enabled::

  [root@controller-6 ~]# nova --debug list

  REQ: curl -i http://192.168.0.2:5000/v2.0/tokens -X POST -H "Content-Type: application/json" -H "Accept: application/json" -H "User-Agent: python-novaclient" -d '{"auth": {"tenantName": "admin", "passwordCredentials": {"username": "admin", "password": "admin"}}}'

  INFO (connectionpool:191) Starting new HTTP connection (1): 192.168.0.2
  DEBUG (connectionpool:283) "POST /v2.0/tokens HTTP/1.1" 200 2702
  RESP: [200] {'date': 'Tue, 06 Aug 2013 13:01:05 GMT', 'content-type': 'application/json', 'content-length': '2702', 'vary': 'X-Auth-Token'}
  RESP BODY: {"access": {"token": {"issued_at": "2013-08-06T13:01:05.616481", "expires": "2013-08-07T13:01:05Z", "id": "c321cd823c8a4852aea4b870a03c8f72", "tenant": {"description": "admin tenant", "enabled": true, "id": "8eee400f7a8a4f35b7a92bc6cb54de42", "name": "admin"}}, "serviceCatalog": [{"endpoints": [{"adminURL": "http://192.168.0.2:8774/v2/8eee400f7a8a4f35b7a92bc6cb54de42", "region": "RegionOne", "internalURL": "http://192.168.0.2:8774/v2/8eee400f7a8a4f35b7a92bc6cb54de42", "id": "6b9563c1e37542519e4fc601b994f980", "publicURL": "http://172.16.1.2:8774/v2/8eee400f7a8a4f35b7a92bc6cb54de42"}], "endpoints_links": [], "type": "compute", "name": "nova"}, {"endpoints": [{"adminURL": "http://192.168.0.2:8080", "region": "RegionOne", "internalURL": "http://192.168.0.2:8080", "id": "4db0e11de3574c889179f499f1e53c7e", "publicURL": "http://172.16.1.2:8080"}], "endpoints_links": [], "type": "s3", "name": "swift_s3"}, {"endpoints": [{"adminURL": "http://192.168.0.2:9292", "region": "RegionOne", "internalURL": "http://192.168.0.2:9292", "id": "960a3ad83e4043bbbc708733571d433b", "publicURL": "http://172.16.1.2:9292"}], "endpoints_links": [], "type": "image", "name": "glance"}, {"endpoints": [{"adminURL": "http://192.168.0.2:8776/v1/8eee400f7a8a4f35b7a92bc6cb54de42", "region": "RegionOne", "internalURL": "http://192.168.0.2:8776/v1/8eee400f7a8a4f35b7a92bc6cb54de42", "id": "055edb2aface49c28576347a8c2a5e35", "publicURL": "http://172.16.1.2:8776/v1/8eee400f7a8a4f35b7a92bc6cb54de42"}], "endpoints_links": [], "type": "volume", "name": "cinder"}, {"endpoints": [{"adminURL": "http://192.168.0.2:8773/services/Admin", "region": "RegionOne", "internalURL": "http://192.168.0.2:8773/services/Cloud", "id": "1e5e51a640f94e60aed0a5296eebdb51", "publicURL": "http://172.16.1.2:8773/services/Cloud"}], "endpoints_links": [], "type": "ec2", "name": "nova_ec2"}, {"endpoints": [{"adminURL": "http://192.168.0.2:8080/", "region": "RegionOne", "internalURL": "http://192.168.0.2:8080/v1/AUTH_8eee400f7a8a4f35b7a92bc6cb54de42", "id": "081a50a3c9fa49719673a52420a87557", "publicURL": "http://172.16.1.2:8080/v1/AUTH_8eee400f7a8a4f35b7a92bc6cb54de42"}], "endpoints_links": [], "type": "object-store", "name": "swift"}, {"endpoints": [{"adminURL": "http://192.168.0.2:35357/v2.0", "region": "RegionOne", "internalURL": "http://192.168.0.2:5000/v2.0", "id": "057a7f8e9a9f4defb1966825de957f5b", "publicURL": "http://172.16.1.2:5000/v2.0"}], "endpoints_links": [], "type": "identity", "name": "keystone"}], "user": {"username": "admin", "roles_links": [], "id": "717701504566411794a9cfcea1a85c1f", "roles": [{"name": "admin"}], "name": "admin"}, "metadata": {"is_admin": 0, "roles": ["90a1f4f29aef48d7bce3ada631a54261"]}}}


  REQ: curl -i http://172.16.1.2:8774/v2/8eee400f7a8a4f35b7a92bc6cb54de42/servers/detail -X GET -H "X-Auth-Project-Id: admin" -H "User-Agent: python-novaclient" -H "Accept: application/json" -H "X-Auth-Token: c321cd823c8a4852aea4b870a03c8f72"

  INFO (connectionpool:191) Starting new HTTP connection (1): 172.16.1.2

Even though initial connection was in 192.168.0.5, then client tries to access public network for Nova API. The reason is because Keystone
returns the list of OpenStack services URLs, and for production-grade deployments it is required to access services over public network.
If you still need to work with OpenStack API without routing configured, tell us your use case on IRC channel **#openstack-fuel** (on freenode) and
we might be able to figure it out together.
