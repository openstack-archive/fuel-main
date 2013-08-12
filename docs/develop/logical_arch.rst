Logical Architecture Diagram
============================

Current architecture uses so-called Metadata via Facter Extension approach.

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
        [Data Model] --> [RPC Consumer (Naily)] : AMQP
        [RPC Consumer (Naily)] --> [RPC Receiver] : AMQP
        [RPC Consumer (Naily)] --> [Orchestrator (Astute)]
        [Orchestrator (Astute)] --> [MCollective]
        [Puppet Master]
    }
    package "Target Node" {
        [MCollective Agent] --> [Puppet]
    }
    actor Web_User
    actor CLI_User
    Web_User --> [JavaScript UI]
    CLI_User --> [Orchestrator (Astute)]

    [JavaScript UI] --> [REST API]

    [Orchestrator (Astute)] --> [Provisioner (Cobbler)] : xmlrpc API

    [MCollective] --> [MCollective Agent]
    [Puppet] --> [Puppet Master]

..    CLI User --> [Provisioner(cobbler)]

