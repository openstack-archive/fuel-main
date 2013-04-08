class osnailyfacter {
  case $deployment_mode {
    "singlenode": { include osnailyfacter::cluster_simple }
    "multinode": { include osnailyfacter::cluster_simple }
    "ha": { include osnailyfacter::cluster_ha }
  }

  include osnailyfacter::network_setup
}
