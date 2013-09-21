Logical Architecture
====================

Current architecture uses so-called "Metadata via Facter Extension"
approach, inspired by blog posts
`self-classifying puppet nodes <http://nuknad.com/2011/02/11/self-classifying-puppet-nodes/>`_,
`pulling a list of hosts from mcollective for puppet <http://nuknad.com/2011/01/07/pulling-a-list-of-hosts-from-mcollective-for-puppet/>`_,
`A Simple Puppet Function to Retrieve Information From the Stored Config
DB <http://blog.thesilentpenguin.com/blog/2012/02/22/a-simple-puppet-function-to-retrieve-information-from-the-stored-config-db/>`_,
`nodeless-puppet example <https://github.com/jordansissel/puppet-examples/tree/master/nodeless-puppet>`_.

In a nutshell, the Fuel deployment orchestration engine `Astute
<https://github.com/Mirantis/astute>`_ manages OS provisioning via
Cobbler, and uses an MCollective plugin to distribute a Facter facts
file that defines node's role and other deployment variables for Puppet.
You can find a detailed breakdown of how this works in the
:doc:`Sequence Diagrams </develop/sequence>`.

Following components are involved in managing this process:

- Astute: deployment orchestrator, manages the Puppet cluster (via
  MCollective) and the Cobbler provisioning service (over XML-RPC)
- Naily: RPC consumer implementing communication between Nailgun and
  Astute over AMQP protocol
- Nailgun [#fn1]_: Web UI backend based on the web.py framework,
  includes following sub-components:

  - Nailgun DB: a relational database holding the current state all
    OpenStack clusters and provisioning tasks
  - Data Model (api/models.py, fixtures/): the definition of NailgunDB
    using SQLAlchemy ORM
  - REST API (api/handlers/): controller layer of the Web UI, receives
    REST requests from the JavaScript UI and routes them to other
    Nailgun components
  - RPC Receiver (rpc/): handles AMQP messages from Astute
  - Task Manager (task/): creates and tracks background tasks

- JavaScript UI (static/js/): Web UI frontend based on Twitter Bootcamp
  framework, communicates with Nailgun using REST API

In the current implementation the deployment business logic is spread
between Nailgun (primarily in Task, Network, and Volume Manager
components) and Astute. Going forward, all logic should be moved from
Astute to Nailgun, and Astute should become a simple executor of tasks
defined by Nailgun.

Communication paths between these components are illustrated on the
Logical Architecture Diagram:

 .. uml::
    package "Master Node" {
        [JavaScript UI]
        package "Nailgun Backend" {
            package "SQL Database" <<Database>> {
                [Nailgun DB]
            }
            [Nailgun DB] --> [Data Model]
            [Data Model] <-- [REST API]
            [RPC Receiver] --> [Nailgun DB]
        }
        [Provisioner (Cobbler)] --> [DHCP, DNS, TFTP]
        [RPC Consumer (Naily)] --> [RPC Receiver] : AMQP
        [RPC Consumer (Naily)] --> [Orchestrator (Astute)] : AMQP
        [Orchestrator (Astute)] --> [MCollective]
        [Puppet Master]
    }
    package "Target Node" {
        [MCollective Agent] --> [Puppet]
    }
    actor Web_User
    actor CLI_User
    Web_User --> [JavaScript UI]
    CLI_User --> [REST API]

    [JavaScript UI] --> [REST API]

    [Orchestrator (Astute)] --> [Provisioner (Cobbler)] : XML-RPC

    [MCollective] --> [MCollective Agent]
    [Puppet] --> [Puppet Master]

..    CLI User --> [Provisioner(cobbler)]

.. rubric:: Footnotes

.. [#fn1] Not to be confused with Nailgun the Java CLI accelerator

