Sequence Diagrams
=================

OS Provisioning
---------------
 .. uml::
    title Nodes Provisioning
    actor WebUser

    box "Physical Server"
        participant NodePXE
        participant NodeAgent
    end box

    NodePXE -> Cobbler: PXE discovery
    Cobbler --> NodePXE: bootstrap OS image
    NodePXE -> Cobbler: network settings request
    Cobbler --> NodePXE: IP, DNS response
    NodePXE -> NodePXE: OS installation
    NodePXE -> NodeAgent: starts agent
    NodePXE -> MC: starts MCollective
    NodeAgent -> Ohai: get info
    Ohai --> NodeAgent: info
    NodeAgent -> NodePXE: get admin node IP
    NodePXE --> NodeAgent: admin node IP
    NodeAgent -> Nailgun: Registration
    |||
    WebUser -> Nailgun: create cluster
    WebUser -> Nailgun: add nodes to cluster
    WebUser -> Nailgun: deploy cluster
    |||
    Nailgun -> Naily: Provision CentOS
    Naily -> Astute: Provision CentOS
    Astute -> Cobbler: Provision CentOS
    Cobbler -> NodePXE: ssh to reboot
    Cobbler --> NodePXE: CentOS image
    NodePXE -> NodeAgent: starts agent
    NodePXE -> MC: starts MC agent
    NodeAgent -> Nailgun: Node metadata

Networks Verification
---------------------
 .. uml::
    title Network Verification
    actor WebUser

    WebUser -> Nailgun: verify networks (cluster #1)
    Nailgun -> Naily: verify nets (100-120 vlans)
    Naily -> Astute: verify nets
    Astute -> MC: start listeners
    MC -> net_probe.py: forks to listen
    MC --> Astute: listening
    Astute -> MC: send frames
    MC -> net_probe.py: send frames
    net_probe.py --> MC: sent
    MC --> Astute: sent

    Astute -> MC: get result
    MC -> net_probe.py: stop listeners
    net_probe.py --> MC: result
    MC --> Astute: result graph
    Astute --> Naily: vlans Ok
    Naily --> Nailgun: response
    Nailgun --> WebUser: response


Details on Cluster Provisioning & Deployment (via Facter extension)
-------------------------------------------------------------------
 .. uml::
    title Cluster Deployment
    actor WebUser

    Nailgun -> Naily: Provision,Deploy
    Naily -> Astute: Provision,Deploy
    Astute -> MC: Type of nodes?
    MC -> Astute: bootstrap
    Astute -> Cobbler: create system,reboot
    Astute -> MC: Type of nodes?

    MC --> Astute: booted in target OS
    Astute --> Naily: provisioned
    Naily --> Nailgun: provisioned
    Nailgun --> WebUser: status on UI
    Astute -> MC: Create /etc/naily.facts

    Astute -> MC: run puppet
    MC -> Puppet: runonce
    Puppet -> Puppet_master: get modules,class
    Puppet_master --> Puppet: modules, class
    Puppet -> Facter: get facts
    Facter --> Puppet: set of facts

    Puppet -> Puppet: applies $role
    Puppet --> MC: done
    MC --> Astute: deploy is done
    Astute --> Naily: deploy is done
    Naily --> Nailgun: deploy is done
    Nailgun --> WebUser: deploy is done

Once deploy and provisioning messages are accepted by Naily, provisioining method is called in Astute.
Provisioning part creates system in Cobbler and calls reboot over Cobbler. Then
Astute uses `MCollective direct addressing mode <http://www.devco.net/archives/2012/06/19/mcollective-direct-addressing-mode.php>`_
to check if all required nodes are available,
include puppet agent on them. If some nodes are not ready yet, Astute waits for a few seconds and does request again.
When nodes are booted in target OS,
Astute uses naily_fact MCollective plugin to post data to a special file /etc/naily.fact on target system.
Data include role and all other variables needed for deployment. Then, Astute calls puppetd MCollective plugin 
to start deployment. Puppet is started on nodes, and requests Puppet master for modules and manifests.
site.pp on Master node defines one common class for every node.
Accordingly, puppet agent starts its run. Modules contain facter extension, which runs before deployment. Extension
reads facts from /etc/naily.fact placed by mcollective, and extends Facter data with these facts, which can be
easily used in Puppet modules. Case structure in running class chooses appropriate class to import, based on $role
variable, received from /etc/naily.fact. It loads and starts to execute. All variables from file are available
like ordinary facts from Facter.

It is possible to use the system without Nailgun and Naily: user creates a YAML file with all required
data, and calls Astute binary script. Script loads data from YAML and instantiates Astute instance
the same way as it's instanciated from Naily.

