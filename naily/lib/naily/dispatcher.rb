#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

require 'naily/reporter'

module Naily
  class Dispatcher
    def initialize(producer)
      @orchestrator = Astute::Orchestrator.new(nil, log_parsing=true)
      @producer = producer
      @default_result = {'status' => 'ready', 'progress' => 100}
      @provisionLogParser = Astute::LogParser::ParseProvisionLogs.new
    end

    def echo(args)
      Naily.logger.info 'Running echo command'
      args
    end

    def download_release(data)
#       message = {
#             'method': 'download_release',
#             'respond_to': 'download_release_resp',
#             'args': {
#                 'task_uuid': task.uuid,
#                 'release_info': {
#                     'release_id': 1,
#                     'redhat':{
#                         'license_type': 'rhsm', #'license_type' in ["rhsm", "rhn"]
#                         'username':'',
#                         'password':''
#                     }
#                 }
#             }
#         }
      Naily.logger.info("'download_release' method called with data: #{data.inspect}")
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      begin
        result = @orchestrator.download_release(reporter, data['args']['task_uuid'], nodes, data['args']['attributes'])
      rescue Timeout::Error
        msg = "Timeout of release download is exceeded."
        Naily.logger.error msg
        reporter.report({'status' => 'error', 'error' => msg})
        return
      end
      report_result(result, reporter)
    end

    def provision(data)
      Naily.logger.info("'provision' method called with data: #{data.inspect}")

      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])

      begin
        Naily.logger.info("Trying to instantiate cobbler engine: #{data['args']['engine'].inspect}")
        engine = Astute::Provision::Cobbler.new(data['args']['engine'])
      rescue
        Naily.logger.error("Error occured during cobbler initializing")
        reporter.report({
                          'status' => 'error',
                          'error' => 'Cobbler can not be initialized',
                          'progress' => 100
                        })
        raise StopIteration
      end
      
      failed_nodes = []
      begin
        reboot_events = {}
        data['args']['nodes'].each do |node|
          begin
            Naily.logger.info("Adding #{node['name']} into cobbler")
            engine.item_from_hash('system', node['name'], node,
                             :item_preremove => true)
          rescue RuntimeError => e
            Naily.logger.error("Error occured while adding system #{node['name']} to cobbler")
            raise e
          end
          Naily.logger.debug("Trying to reboot node: #{node['name']}")
          reboot_events[node['name']] = engine.power_reboot(node['name'])
        end
        begin
          Naily.logger.debug("Waiting for reboot to be complete: nodes: #{reboot_events.keys}")
          failed_nodes = []
          Timeout::timeout(Naily.config.reboot_timeout) do
            while not reboot_events.empty?
              reboot_events.each do |node_name, event_id|
                event_status = engine.event_status(event_id)
                Naily.logger.debug("Reboot task status: node: #{node_name} status: #{event_status}")
                if event_status[2] =~ /^failed$/
                  Naily.logger.error("Error occured while trying to reboot: #{node_name}")
                  reboot_events.delete(node_name)
                  failed_nodes << node_name
                elsif event_status[2] =~ /^complete$/
                  Naily.logger.debug("Successfully rebooted: #{node_name}")
                  reboot_events.delete(node_name)
                end
              end
              sleep(5)
            end
          end
        rescue Timeout::Error => e
          Naily.logger.debug("Reboot timeout: reboot tasks not completed for nodes #{reboot_events.keys}")
          raise e
        end
      rescue RuntimeError => e
        Naily.logger.error("Error occured while provisioning: #{e.inspect}")
        reporter.report({
                          'status' => 'error',
                          'error' => 'Cobbler error',
                          'progress' => 100
                        })
        engine.sync
        raise StopIteration
      end
      engine.sync
      if failed_nodes.empty?
        report_result({}, reporter)
      else
        reporter.report({
                          'status' => 'error',
                          'error' => "Nodes failed to reboot: #{failed_nodes.inspect}",
                          'progress' => 100
                        })
        raise StopIteration
      end
      return
    end

    def deploy(data)
      Naily.logger.info("'deploy' method called with data: #{data.inspect}")

      # Following line fixes issues with uids: it should always be string
      data['args']['nodes'].map { |x| x['uid'] = x['uid'].to_s }
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      nodes_uids = nodes.map { |n| n['uid'] }
      time = Time::now.to_f
      nodes_not_booted = nodes.map { |n| n['uid'] }
      Naily.logger.info "Starting OS provisioning for nodes: #{nodes_not_booted.join(',')}"
      begin
        @provisionLogParser.prepare(nodes)
      rescue Exception => e
        Naily.logger.warn "Some error occurred when prepare LogParser: #{e.message}, trace: #{e.backtrace.inspect}"
      end
      time = 10 + time - Time::now.to_f
      sleep (time) if time > 0 # Wait while nodes going to reboot. Sleep not greater than 10 sec.
      begin
        Timeout::timeout(Naily.config.provisioning_timeout) do  # Timeout for booting target OS
          while true
            time = Time::now.to_f
            types = @orchestrator.node_type(reporter, data['args']['task_uuid'], nodes, 2)
            types.each do |t|
              Naily.logger.debug("Got node types: uid=#{t['uid']} type=#{t['node_type']}")
            end
            Naily.logger.debug("Not target nodes will be rejected")
            target_uids = types.reject{|n| n['node_type'] != 'target'}.map{|n| n['uid']}
            Naily.logger.debug "Not provisioned: #{nodes_not_booted.join(',')}, got target OSes: #{target_uids.join(',')}"
            if nodes.length == target_uids.length
              Naily.logger.info "All nodes #{target_uids.join(',')} are provisioned."
              break
            else
              Naily.logger.debug("Nodes list length is not equal to target nodes list length: #{nodes.length} != #{target_uids.length}")
            end
            nodes_not_booted = nodes_uids - types.map { |n| n['uid'] }
            begin
              nodes_progress = @provisionLogParser.progress_calculate(nodes_uids, nodes)
              nodes_progress.each do |n|
                if target_uids.include?(n['uid'])
                  n['progress'] = 100
                  # TODO(mihgen): should we change status only once?
                  n['status'] = 'provisioned'
                end
              end
              reporter.report({'nodes' => nodes_progress})
            rescue Exception => e
              Naily.logger.warn "Some error occurred when parse logs for nodes progress: #{e.message}, trace: #{e.backtrace.inspect}"
            end
            time = 5 + time - Time::now.to_f
            sleep (time) if time > 0 # Sleep not greater than 5 sec.
          end
          # We are here if jumped by break from while cycle
        end
      rescue Timeout::Error
        msg = "Timeout of provisioning is exceeded."
        Naily.logger.error msg
        error_nodes = nodes_not_booted.map { |n| {'uid' => n,
                                                  'status' => 'error',
                                                  'error_msg' => msg,
                                                  'progress' => 100,
                                                  'error_type' => 'provision'} }
        reporter.report({'status' => 'error', 'error' => msg, 'nodes' => error_nodes})
        return
      end

      nodes_progress = nodes.map do |n|
        {'uid' => n['uid'], 'progress' => 100, 'status' => 'provisioned'}
      end
      reporter.report({'nodes' => nodes_progress})

      begin
        result = @orchestrator.deploy(reporter, data['args']['task_uuid'], nodes, data['args']['attributes'])
      rescue Timeout::Error
        msg = "Timeout of deployment is exceeded."
        Naily.logger.error msg
        reporter.report({'status' => 'error', 'error' => msg})
        return
      end

      report_result(result, reporter)
    end

    def verify_networks(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      args = data['args']
      result = @orchestrator.verify_networks(reporter, data['args']['task_uuid'], args['nodes'])
      report_result(result, reporter)
    end

    def remove_nodes(data)
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      nodes = data['args']['nodes']
      provision_engine = Astute::Provision::Cobbler.new(data['args']['engine'])
      data['args']['engine_nodes'].each do |name|
        if provision_engine.system_exists(name)
          Naily.logger.info("Removing system from cobbler: #{name}")
          provision_engine.remove_system(name)
          if not provision_engine.system_exists(name)
            Naily.logger.info("System has been successfully removed from cobbler: #{name}")
          else
            Naily.logger.error("Cannot remove node from cobbler: #{name}")
          end
        else
          Naily.logger.info("System is not in cobbler: #{name}")
        end
      end
      Naily.logger.debug("Cobbler syncing")
      provision_engine.sync
      result = @orchestrator.remove_nodes(reporter, data['args']['task_uuid'], nodes)
      report_result(result, reporter)
    end

    private
    def report_result(result, reporter)
      result = {} unless result.instance_of?(Hash)
      status = @default_result.merge(result)
      reporter.report(status)
    end
  end
end
