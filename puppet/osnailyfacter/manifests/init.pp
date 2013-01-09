class osnailyfacter {
  case $deployment_mode {
    "singlenode_compute": { include osnailyfacter::cluster_simple }
    "multinode_compute": { include osnailyfacter::cluster_simple }
    "ha_compute": { include osnailyfacter::cluster_ha }
  }

  include osnailyfacter::network_setup
}
