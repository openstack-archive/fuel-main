require 'json'
require 'timeout'
require 'mcollective'

PUPPET_TIMEOUT = 30*60

module Orchestrator
  class Orchestrator
    include MCollective::RPC

    private
    def check_mcollective_result(stats, log=true)
      # Following error might happen because of misconfiguration, ex. direct_addressing = 1 only on client
      raise "MCollective has failed and didn't even return anything. Check it's logs." if stats.length == 0
      result_data = []
      stats.each do |agent|
        status = agent.results[:statuscode]
        result_data << agent.results['data']
        if status != 0
          @logger.error "MC agent #{agent.agent} has failed, results: #{agent.results.inspect}"
          raise "MCollective id='#{agent.results[:sender]}' call failed in agent '#{agent.agent}'"
        else
          @logger.debug "MC agent #{agent.agent} succeeded, results: #{agent.results.inspect}" if log
        end
      end
      return result_data
    end

    def wait_until_puppet_done(mc, previous_runs)
      # Wait for first node is done, than check the next one
      # Load to mcollective is reduced by checking only one machine at time in a set
      # In fact we need to know if whole set of machines finished deployment
      previous_runs.each do |res|
        prev_run = res['ts']
        last_run = prev_run
        while last_run == prev_run
          mc.discover(:nodes => [res['sender']])
          puppet_status = mc.status
          # logging to false, otherwise we get a message every second
          check_mcollective_result(puppet_status, log=false)
          last_run = puppet_status[0].results[:data][:lastrun]
          sleep 1 if last_run == prev_run
        end
      end
    end

    public
    def initialize
      @logger = ::Orchestrator.logger
    end

    def deploy(reporter, nodes)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      @logger.debug "nailyfact - storing metadata for nodes: #{macs.join(',')}"

      nodes.each do |node|
        mc = rpcclient("nailyfact")
        mc.progress = false
        mc.discover(:nodes => [node['mac'].gsub(":", "")])
        metadata = {'role' => node['role']}

        # This is synchronious RPC call, so we are sure that data were sent and processed remotely
        stats = mc.post(:value => metadata.to_json)
        check_mcollective_result(stats)
      end

      reporter.report({'progress' => 1})

      mc = rpcclient("puppetd")
      mc.progress = false
      mc.discover(:nodes => macs)
      puppet_status = mc.status
      check_mcollective_result(puppet_status)

      # In results :lastrun we get the time when Puppet finished it's work last time
      previous_runs = puppet_status.map { |res| {'sender' => res.results[:sender],
                                                 'ts' => res.results[:data][:lastrun]} }

      check_mcollective_result(mc.runonce)

      reporter.report({'progress' => 2})

      @logger.debug "Waiting for puppet to finish deploymen on all nodes (timeout = #{PUPPET_TIMEOUT} sec)..."
      time_before = Time.now
      Timeout::timeout(PUPPET_TIMEOUT) do  # 30 min for deployment to be done
        wait_until_puppet_done(mc, previous_runs)
      end
      time_spent = Time.now - time_before
      @logger.info "Spent #{time_spent} seconds on puppet run for following nodes(macs): #{nodes.map {|n| n['mac']}.join(',')}"

      reporter.report({'progress' => 100})
    end

    def verify_networks(reporter, nodes, networks)
      macs = nodes.map {|n| n['mac'].gsub(":", "")}
      mc = rpcclient("net_probe")
      mc.progress = false
      mc.discover(:nodes => macs)

      stats = mc.start_frame_listeners({'iflist' => 'eth0'})
      check_mcollective_result(stats)
      
      stats = mc.send_probing_frames({'interfaces' => {'eth0' => networks.map {|n| n['vlan_id']}.join(',')}})
      check_mcollective_result(stats)

      sleep 5
      stats = mc.get_probing_info
      printrpc mc.get_probing_info
    end
  end

end
