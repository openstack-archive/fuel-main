Logical Architecture Diagram
============================

Metadata via Facter Extension
-----------------------------
 .. uml::
    package "Master Node" {
        [JavaScript UI]
        package "Nailgun backend" {
            package "Database" <<Database>> {
                [SQL DB]
            }
            [SQL DB] --> [Data Model]
            [Data Model] <-- [REST API(web.py)]
            [Receiver] --> [SQL DB]
        }
        [Provisioner(cobbler)] --> [DHCP, DNS, TFTP]
        [Data Model] --> [Async RPC consumer(Naily)] : AMQP
        [Async RPC consumer(Naily)] --> [Receiver] : AMQP
        [Async RPC consumer(Naily)] --> [Orchestrator]
        [Orchestrator] --> [MCollective]
    }
    package "Target Node" {
        [MCollective Agent] --> [Puppet]
    }
    actor Web_User
    actor CLI_User
    Web_User --> [JavaScript UI]
    CLI_User --> [Orchestrator]

    [JavaScript UI] --> [REST API(web.py)]

    [Data Model] --> [Provisioner(cobbler)] : xmlrpc API

    [MCollective] --> [MCollective Agent]
    [Puppet] --> [Puppet Master]

..    CLI_User --> [Provisioner(cobbler)]


Metadata via Puppet ENC (part of architecture)
----------------------------------------------

This is alternative possible architecture.
See corresponding sequence diagram for details: :ref:`deploy_via_enc_sequence`.

 .. uml::
    package "Master Node" {
        [Async RPC consumer(Naily)] --> [Orchestrator]
        [Orchestrator] --> [MCollective]
        [Orchestrator] <-- [YAML data source]
        [Puppet Master] --> [ENC Script]
        [ENC Script] --> [YAML data source]
    }
    package "Target Node" {
        [MCollective Agent] --> [Puppet]
    }
    actor CLI_User
    CLI_User --> [YAML data source]
    CLI_User --> [Orchestrator]

    [MCollective] --> [MCollective Agent]
    [Puppet] --> [Puppet Master]
