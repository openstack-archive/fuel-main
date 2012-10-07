Sequence Diagram
================

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
    Nailgun -> Cobbler: Provision CentOS
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


Details on Cluster Deployment (via Facter extension)
----------------------------------------------------
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
    
Once deploy message is accepted by Naily, it asks Orchestrator if nodes are ready.
Orchestrator, on its turn, uses `MCollective direct addressing mode <http://www.devco.net/archives/2012/06/19/mcollective-direct-addressing-mode.php>`_
to check if all required nodes are available,
include puppet agent on them. Orchestrator responds back to Naily with this information.
If some nodes are not ready yet, Naily waits for a few seconds and does request again. Otherwise, Naily calls deploy
on Orchestrator, passing nodes, roles, network data and other attributes defined by user in WebUI.
Orchestrator uses naily_fact MCollective plugin to post data to a special file /etc/naily.fact on target system.
Data include role and all other variables needed for deployment. Then, Orchestrator calls puppetd MCollective plugin 
to start deployment. Puppet is started on nodes, and requests Puppet master for modules and manifests.
site.pp on Master node defines one common class for every node.
Accordingly, puppet agent starts its run. Modules contain facter extension, which runs before deployment. Extension
reads facts from /etc/naily.fact placed by mcollective, and extends Facter data with these facts, which can be
easily used in Puppet modules. Case structure in running class chooses appropriate class to import, based on $role
variable, received from /etc/naily.fact. It loads and starts to execute. All variables from file are available
like ordinary facts from Facter.
Inspired by blog post `self-classifying puppet nodes <http://nuknad.com/2011/02/11/self-classifying-puppet-nodes/>`_.
Some other details on approach: `nodeless-puppet example <https://github.com/jordansissel/puppet-examples/tree/master/nodeless-puppet>`_.
It could be possible to use just special file and not to extend facts of Facter, just load JSON data straight
during Puppet recipes execution, however additional research should be done.
Last notice on how to work with the system without Nailgun and Naily: user creates a YAML file with all required
data, and calls Orchestrator binary script. Script loads data from YAML and instantiates Orchestrator instance
the same way as it's instanciated from Naily. Messages come to STDOUT instead of file logger.

.. _deploy_via_enc_sequence:

Alternative Implementation for deployment via ENC
-------------------------------------------------
 .. uml::
    title Diagram of ALTERNATIVE Implementation of Cluster Deployment
    autonumber
    actor WebUser
    
    Nailgun -> Naily: Deploy cluster
    Naily -> YAML_file: Store configuration
    Naily -> Orchestrator: Deploy
    Orchestrator -> YAML_file: get data
    YAML_file --> Orchestrator: data
    Orchestrator -> MC: nodes ready?
    MC --> Orchestrator: ready
    Orchestrator --> Naily: ready
    Naily -> Nailgun: nodes booted
    Nailgun --> WebUser: status on UI
    |||
    Orchestrator -> MC: run puppet
    MC -> Puppet: runonce
    Puppet -> Puppet_master: get modules,class
    Puppet_master -> ENC: get class
    ENC -> YAML_file: get class
    YAML_file --> ENC: class to deploy
    ENC --> Puppet_master: class
    Puppet_master --> Puppet: modules, class
    Puppet -> Puppet: applies $role
    Puppet --> MC: done
    MC --> Orchestrator: deploy is done
    Orchestrator -> YAML_file: update info
    Orchestrator --> Naily: deploy is done
    Naily --> Nailgun: deploy is done
    Nailgun --> WebUser: deploy is done

Alternative schema of deployment is different in following:

* Naily stores all data about deployment into YAML file before the deployment, and then calls Orchestrator
* Orchestrator loads nodes information from YAML and calls puppet via MCollective
* Puppet requests data from Puppet master
* Puppet uses `ENC extension <http://docs.puppetlabs.com/guides/external_nodes.html>`_ to get information what
  classes should be applied on particular node. If try to explain in a few
  words what ENC is - it is Puppet Master's extension to call external user defined script
* ENC script loads all required data from YAML file
* YAML file could be replaced by some NoSQL DB

Comparison of deployment approaches
-----------------------------------

Data from Facter
^^^^^^^^^^^^^^^^
Pros:

* Easy. Put file on node via MCollective, and we know what will be executed there. It's easy to check what have been
  executed last time.
* No additional stateful components. Otherwise it could lead to data inconsistency
* Easy to switch into configuration without Puppet Master or even replace it to Chef Solo
* Requires time to place data on nodes before puppet run, and implementation in syncronious way - puppet should not
  run before the node receive it's role.

Cons:

* Doesn't look like a "Puppet" way, when desired state of Cluster should be defined beforeahead and Puppet
  will converge the existing state to the desired state

Data from ENC
^^^^^^^^^^^^^
Pros:

* "Puppet" way, everything what is needed is defined in YAML file
* All information could be found in one place - YAML file

Cons:

* Naily should know the data structure in YAML file to do the merge. (however it can just call Orchestrator with
  metadata, and Orchestrator will write data to YAML file)
* Requires additional stateful component - YAML file, what may lead to data inconsistency
* Puppet Master must be installed on the same node as Orchestrator (to access YAML file). Even if YAML file
  is replaced to NoSQL DB, ENC script still has to be present on Puppet Master node.
* With increase of deployment complexity and metadata, YAML file will increase in size. It also should contain
  information about all clusters and all nodes consequently, which could become a bottleneck for loading data
  in case of hundrends nodes and thousand requests. Separation of YAML structure in cluster-based will not help
  because there will be need to pass cluster identifier to puppet, what's unclear how to do besides facter
  extension.
* More complex code for Naily(or Orchestrator) is required to do merges of existing data in YAML file and new data,
  code to prevent concurrency issues. It would be even more complex with Updates feature, when it would require
  of a sequence of actions performed in a specific order.
