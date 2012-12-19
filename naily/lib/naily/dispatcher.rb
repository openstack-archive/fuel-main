require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new
      @producer = producer
      @default_result = {'status' => 'ready', 'progress' => 100}
      @provision_progress_part = 0.8
      @anaconda_log_portion = 40000 # Size of block which reads for pattern searching.
      @ananconda_log_patterns = [
        {'pattern' => 'Running kickstart %%pre script', 'progress' => 0.08},
        {'pattern' => 'to step enablefilesystems', 'progress' => 0.09},
        {'pattern' => 'to step reposetup', 'progress' => 0.13},
        {'pattern' => 'to step installpackages', 'progress' => 0.16},
        {'pattern' => 'Installing',
          'number' => 210, # Now it install 205 packets. Add 5 packets for growth in future.
          'p_min' => 0.16, # min percent
          'p_max' => 0.87 # max percent
          },
        {'pattern' => 'to step postinstallconfig', 'progress' => 0.87},
        {'pattern' => 'to step dopostaction', 'progress' => 0.92},
        {'pattern' => 'SEPARATOR', 'progress' => 0}
        ].reverse
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def deploy(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      time = Time::now.to_f
      nodes_not_booted = nodes.map { |n| n['uid'] }
      Naily.logger.info "Starting OS provisioning for nodes: #{nodes_not_booted.join(',')}" 
      add_anaconda_log_separator(nodes)
      time = 10 + time - Time::now.to_f
      sleep (time) if time > 0 # Wait while nodes going to reboot. Sleep not greater than 10 sec.
      begin
        Timeout::timeout(20 * 60) do  # 20 min for booting target OS
          while true
            time = Time::now.to_f
            types = @orchestrator.node_type(reporter, data['args']['task_uuid'], nodes, 5)
            target_uids = types.reject{|n| n['node_type'] != 'target'}.map{|n| n['uid']}
            Naily.logger.debug "Not provisioned: #{nodes_not_booted.join(',')}, got target OSes: #{target_uids.join(',')}" 
            if nodes.length == target_uids.length
              Naily.logger.info "All nodes #{target_uids.join(',')} are provisioned."
              break
            end
            nodes_not_booted = nodes.map { |n| n['uid'] } - types.map { |n| n['uid'] }
            all_progress = 0
            nodes_progress = provisioning_progress_calculate(nodes)
            nodes_progress.each do |n|
              if target_uids.include?(n['uid'])
                all_progress += 100 # 100%
                n['progress'] = 100
                # TODO(mihgen): should we change status only once?
                n['status'] = 'provisioned'
              else
                all_progress += n['progress']
              end
            end

            all_progress = (all_progress * @provision_progress_part / nodes.size).to_i
            reporter.report({'progress' => all_progress, 'nodes' => nodes_progress})
            time = 5 + time - Time::now.to_f
            sleep (time) if time > 0 # Sleep not greater than 5 sec.
          end
          # We are here if jumped by break from while cycle
        end
      rescue Timeout::Error
        Naily.logger.error "Provisioning has timed out"
        error_msg = "Timeout of provisioning is exceeded for nodes: '#{nodes_not_booted.join(',')}'"
        error_nodes = nodes_not_booted.map { |n| {'uid' => n,
                                                  'status' => 'error',
                                                  'progress' => 100,
                                                  'error_type' => 'provision'} }
        reporter.report({'status' => 'error', 'error' => error_msg, 'nodes' => error_nodes})
        return
      end

      reporter.report({'progress' => (@provision_progress_part * 100).to_i})
      result = @orchestrator.deploy(reporter, data['args']['task_uuid'], nodes, data['args']['attributes'], @provision_progress_part)
      report_result(result, reporter)
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      args = data['args']
      result = @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'], args['networks'])
      report_result(result, reporter)
    end

    def remove_nodes(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      result = @orchestrator.remove_nodes(reporter, data['args']['task_uuid'], nodes)
      report_result(result, reporter)
    end

    private
    def provisioning_progress_calculate(nodes)
      return 0 if nodes.empty?
      nodes_progress = []
      nodes.each do |node|
        path = "/var/log/remote/#{node['ip']}/install/anaconda.log"
        nodes_progress << {
          'uid' => node['uid'],
          'progress' => (get_anaconda_log_progress(path)*100).to_i # Return percent of progress
        }
      end
      return nodes_progress
    end

    def add_anaconda_log_separator(nodes)
      nodes.each do |node|
        path = "/var/log/remote/#{node['ip']}/install/anaconda.log"
        File.open(path, 'a') {|fo| fo.puts "\n\nSEPARATOR" } if File.readable?(path)
      end
    end

    def get_anaconda_log_progress(file)
      return 0 unless File.readable?(file)
      File.open(file) do |fo|
        if fo.stat.size > @anaconda_log_portion
          fo.pos = fo.stat.size - @anaconda_log_portion
          block = fo.read(@anaconda_log_portion).split("\n")
        else
          block = fo.read(fo.stat.size).split("\n")
        end

        while true
          string = block.pop
          return 0 unless string # If we found nothing
          @ananconda_log_patterns.each do |pattern|
            if string.include?(pattern['pattern'])
              return pattern['progress'] if pattern['progress']
              if pattern['number']
                string = block.pop
                counter = 1
                while string
                  counter += 1 if string.include?(pattern['pattern'])
                  string = block.pop
                end
                progress = counter.to_f / pattern['number']
                progress = 1 if progress > 1
                progress = pattern['p_min'] + progress * (pattern['p_max'] - pattern['p_min'])
                return progress
              end
              Naily.logger.warn("Wrong pattern #{pattern.inspect} defined for calculating progress via Anaconda log.")
            end
          end
        end
      end
    end

    def report_result(result, reporter)
      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end
  end
end
