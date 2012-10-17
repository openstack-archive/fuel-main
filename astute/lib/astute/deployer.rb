require 'json'
require 'timeout'

PUPPET_TIMEOUT = 30*60

module Astute
  module Deployer
    private

    def self.wait_until_puppet_done(puppetd, previous_run_status)
      # Wait for first node is done, than check the next one
      # Load to mcollective is reduced by checking only one machine at time in a set
      # In fact we need to know if whole set of machines finished deployment
      previous_run_status.each do |res|
        prev_run = res.results[:data][:lastrun]
        last_run = prev_run
        while last_run == prev_run
          puppetd.discover(:nodes => [res.results[:sender]])
          puppet_status = puppetd.status
          # logging to false, otherwise we get a message every second
          last_run = puppet_status[0].results[:data][:lastrun]
          sleep 1 if last_run == prev_run
        end
      end
    end

    public
    def self.puppet_deploy_with_polling(ctx, nodes)
      if nodes.empty?
        Astute.logger.info "#{ctx.task_id}: Nodes to deploy are not provided. Do nothing."
        return false
      end
      uids = nodes.map {|n| n['uid'].gsub(":", "")}
      puppetd = MClient.new(ctx, "puppetd", uids)
      puppet_status = puppetd.status

      puppetd.runonce

      Astute.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        # Yes, we polling here and yes, it's temporary.
        # As a better implementation we can later use separate queue to get result, ex. http://www.devco.net/archives/2012/08/19/mcollective-async-result-handling.php
        # or we can rewrite puppet agent not to fork, and increase ttl for mcollective RPC.
        wait_until_puppet_done(puppetd, puppet_status)
      end
      time_spent = Time.now - time_before
      Astute.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(uids): #{nodes.map {|n| n['uid']}.join(',')}"
    end
  end
end
  
