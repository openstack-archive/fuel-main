class osnailyfacter {
  $cluster_mode = "simple"
  case $cluster_mode {
    "simple": { include osnailyfacter::cluster_simple }
    "ha": { include osnailyfacter::cluster_ha }
  }

  include osnailyfacter::network_setup
}
