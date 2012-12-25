class osnailyfacter {
  case $deployment_mode {
    "simple_compute": { include osnailyfacter::cluster_simple }
    "ha_compute": { include osnailyfacter::cluster_ha }
  }

  include osnailyfacter::network_setup
}
