Sequence Diagram
================

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
    Nailgun -> Cobbler: Provision CentOS
    Cobbler -> NodePXE: ssh to reboot
    Cobbler --> NodePXE: CentOS image
    NodePXE -> NodeAgent: starts agent
    NodePXE -> MC: starts MC agent
    NodeAgent -> Nailgun: Node metadata


 .. uml::
    title Cluster Deployment
    actor WebUser

    Nailgun -> Naily: Deploy cluster
    Naily -> Orchestrator: Are nodes ready?
    Orchestrator -> MC: Are nodes?
    MC --> Orchestrator: ready
    Orchestrator --> Naily: ready
    Naily -> Nailgun: nodes booted
    Nailgun --> WebUser: status on UI
    Naily -> Orchestrator: deploy
    Orchestrator -> MC: set $role
    MC -> Facter: set $role
    Facter --> MC: $role stored
    MC --> Orchestrator: roles are set

    Orchestrator -> MC: run puppet
    MC -> Puppet: runonce
    Puppet -> Puppet_master: get modules,class
    Puppet_master --> Puppet: modules, class
    Puppet -> Facter: get facts
    Facter --> Puppet: $role

    Puppet -> Puppet: applies $role
    Puppet --> MC: done
    MC --> Orchestrator: deploy is done
    Orchestrator --> Naily: deploy is done
    Naily --> Nailgun: deploy is done
    Nailgun --> WebUser: deploy is done
    
 .. uml::
    title Network Verification
    actor WebUser

    WebUser -> Nailgun: verify networks (cluster #1)
    Nailgun -> Naily: verify nets (100-120 vlans)
    Naily -> Orchestrator: verify nets
    Orchestrator -> MC: start listeners
    MC -> net_probe.py: forks to listen
    MC --> Orchestrator: listening
    Orchestrator -> MC: send frames
    MC -> net_probe.py: send frames
    net_probe.py --> MC: sent
    MC --> Orchestrator: sent

    Orchestrator -> MC: get result
    MC -> net_probe.py: stop listeners
    net_probe.py --> MC: result
    MC --> Orchestrator: result graph
    Orchestrator --> Naily: vlans Ok
    Naily --> Nailgun: response
    Nailgun --> WebUser: response
