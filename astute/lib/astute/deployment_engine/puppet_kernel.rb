class Astute::DeploymentEngine::PuppetKernel < Astute::DeploymentEngine
  # NOTE(mihgen): Not completed
  def deploy_piece(nodes, attrs)
    return false unless validate_nodes(nodes)
    case nodes[0]['role']
    when "controller"
      classes = {"nailytest::test_rpuppet" => {"rpuppet" => ["controller", "privet"]}}
      Astute::RpuppetDeployer.rpuppet_deploy(@ctx, nodes, attrs, classes)
      # network_data = calculate_networks(node['network_data'])
    end
  end
end
