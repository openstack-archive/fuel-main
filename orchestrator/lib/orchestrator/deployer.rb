require 'json'
require 'timeout'

PUPPET_TIMEOUT = 30*60

module Orchestrator
  private

  def wait_until_puppet_done(puppetd, previous_runs)
    # Wait for first node is done, than check the next one
    # Load to mcollective is reduced by checking only one machine at time in a set
    # In fact we need to know if whole set of machines finished deployment
    previous_runs.each do |res|
      prev_run = res['ts']
      last_run = prev_run
      while last_run == prev_run
        puppetd.discover(:nodes => [res['sender']])
        puppet_status = puppetd.status
        # logging to false, otherwise we get a message every second
        last_run = puppet_status[0].results[:data][:lastrun]
        sleep 1 if last_run == prev_run
      end
    end
  end

  public
  def puppet_deploy_with_polling(ctx, nodes)
    if nodes.empty?
      ::Orchestrator.logger.info "#{ctx.task_id}: Nodes to deploy are not provided. Do nothing."
      return false
    end
    macs = nodes.map {|n| n['mac'].gsub(":", "")}
    puppetd = MClient.new(ctx, "puppetd", macs)
    puppet_status = puppetd.status

    # In results :lastrun we get the time when Puppet finished it's work last time
    previous_runs = puppet_status.map { |res| {'sender' => res.results[:sender],
                                               'ts' => res.results[:data][:lastrun]} }

    puppetd.runonce

    ::Orchestrator.logger.debug "Waiting for puppet to finish deployment on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
    time_before = Time.now
    Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
      # Yes, we polling here and yes, it's temporary.
      # As a better implementation we can later use separate queue to get result, ex. http://www.devco.net/archives/2012/08/19/mcollective-async-result-handling.php
      # or we can rewrite puppet agent not to fork, and increase ttl for mcollective RPC.
      wait_until_puppet_done(puppetd, previous_runs)
    end
    time_spent = Time.now - time_before
    ::Orchestrator.logger.info "#{ctx.task_id}: Spent #{time_spent} seconds on puppet run for following nodes(macs): #{nodes.map {|n| n['mac']}.join(',')}"

  end
end
  
