class nailytest::network_setup {

include puppet-network
        create_resources(network_config,parsejson($network_data))
}

