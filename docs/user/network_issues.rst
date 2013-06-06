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

  REQ: curl -i http://192.168.0.5:5000/v2.0/tokens -X POST -H "Content-Type: application/json" -H "Accept: application/json" -H "User-Agent: python-novaclient" -d '{"auth": {"tenantName": "admin", "passwordCredentials": {"username": "admin", "password": "admin"}}}'

  INFO (connectionpool:191) Starting new HTTP connection (1): 192.168.0.5
  DEBUG (connectionpool:283) "POST /v2.0/tokens HTTP/1.1" 200 2695
  RESP: [200] {'date': 'Thu, 06 Jun 2013 09:50:22 GMT', 'content-type': 'application/json', 'content-length': '2695', 'vary': 'X-Auth-Token'}
  RESP BODY: {"access": {"token": {"issued_at": "2013-06-06T09:50:21.950681", "expires": "2013-06-07T09:50:21Z", "id": "d9ab5c927bcb410d9e9ee5bdea3ea020", "tenant": {"description": "admin tenant", "enabled": true, "id": "1a491e1416d041da93daae1dc8af6d07", "name": "admin"}}, "serviceCatalog": [{"endpoints": [{"adminURL": "http://192.168.0.5:8774/v2/1a491e1416d041da93daae1dc8af6d07", "region": "RegionOne", "internalURL": "http://192.168.0.5:8774/v2/1a491e1416d041da93daae1dc8af6d07", "id": "0281b33145d0417a976b8d0e9bab08b8", "publicURL": "http://240.0.1.5:8774/v2/1a491e1416d041da93daae1dc8af6d07"}], "endpoints_links": [], "type": "compute", "name": "nova"}, {"endpoints": [{"adminURL": "http://192.168.0.5:8080", "region": "RegionOne", "internalURL": "http://192.168.0.5:8080", "id": "3c8dea92d2e046c8bf188b2d357425a1", "publicURL": "http://240.0.1.5:8080"}], "endpoints_links": [], "type": "s3", "name": "swift_s3"}, {"endpoints": [{"adminURL": "http://192.168.0.5:9292", "region": "RegionOne", "internalURL": "http://192.168.0.5:9292", "id": "d9a08cc4f1294e4c8748966363468089", "publicURL": "http://240.0.1.5:9292"}], "endpoints_links": [], "type": "image", "name": "glance"}, {"endpoints": [{"adminURL": "http://192.168.0.5:8776/v1/1a491e1416d041da93daae1dc8af6d07", "region": "RegionOne", "internalURL": "http://192.168.0.5:8776/v1/1a491e1416d041da93daae1dc8af6d07", "id": "7563a55f46584e149b822507811b868c", "publicURL": "http://240.0.1.5:8776/v1/1a491e1416d041da93daae1dc8af6d07"}], "endpoints_links": [], "type": "volume", "name": "cinder"}, {"endpoints": [{"adminURL": "http://192.168.0.5:8773/services/Admin", "region": "RegionOne", "internalURL": "http://192.168.0.5:8773/services/Cloud", "id": "2f5d062c52b24f85a193306809c9600c", "publicURL": "http://240.0.1.5:8773/services/Cloud"}], "endpoints_links": [], "type": "ec2", "name": "nova_ec2"}, {"endpoints": [{"adminURL": "http://192.168.0.5:8080/", "region": "RegionOne", "internalURL": "http://192.168.0.5:8080/v1/AUTH_1a491e1416d041da93daae1dc8af6d07", "id": "2bb237d0db004cd08f1be57fd14e2892", "publicURL": "http://240.0.1.5:8080/v1/AUTH_1a491e1416d041da93daae1dc8af6d07"}], "endpoints_links": [], "type": "object-store", "name": "swift"}, {"endpoints": [{"adminURL": "http://192.168.0.5:35357/v2.0", "region": "RegionOne", "internalURL": "http://192.168.0.5:5000/v2.0", "id": "2fa7c6deb7ad42aabab7935bc269bb4e", "publicURL": "http://240.0.1.5:5000/v2.0"}], "endpoints_links": [], "type": "identity", "name": "keystone"}], "user": {"username": "admin", "roles_links": [], "id": "d9321ac604694ffb9e4a8517292f55d6", "roles": [{"name": "admin"}], "name": "admin"}, "metadata": {"is_admin": 0, "roles": ["c80a3ab61b2c42b4bcacb4b316856618"]}}}


  REQ: curl -i http://240.0.1.5:8774/v2/1a491e1416d041da93daae1dc8af6d07/servers/detail -X GET -H "X-Auth-Project-Id: admin" -H "User-Agent: python-novaclient" -H "Accept: application/json" -H "X-Auth-Token: d9ab5c927bcb410d9e9ee5bdea3ea020"

  INFO (connectionpool:191) Starting new HTTP connection (1): 240.0.1.5

Even though initial connection was in 192.168.0.5, then client tries to access public network for Nova API. The reason is because Keystone
returns the list of OpenStack services URLs, and for production-grade deployments it is required to access services over public network.
If you still need to work with OpenStack API without routing configured, tell us your use case on IRC channel **#openstack-fuel** (on freenode) and
we might be able to figure it out together.
