require 'json'
require 'timeout'

module Astute
  module RpuppetDeployer
    def self.rpuppet_deploy(ctx, nodes, attrs, classes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to deploy are not provided. Do nothing."
        return false
      end
      uids = nodes.map {|n| n['uid']}
      rpuppet = MClient.new(ctx, "rpuppet", uids)

      data = {"parameters" => data,
              "classes" => classes,
              "environment" => "production"}

      Astute.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        rpuppet.run(:data => data.to_json)
      end
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
