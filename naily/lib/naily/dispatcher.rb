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
      # Example of message = {
      # {'method': 'download_release',
      # 'respond_to': 'download_release_resp',
      # 'args':{
      #     'task_uuid': 'task UUID',
      #     'release_info':{
      #         'release_id': 'release ID',
      #         'redhat':{
      #             'license_type' :"rhn" or "rhsm",
      #             'username': 'username',
      #             'password': 'password',
      #             'satellite': 'satellite host (for RHN license)'
      #             'activation_key': 'activation key (for RHN license)'
      #         }
      #     }
      # }}
      Naily.logger.info("'download_release' method called with data: #{data.inspect}")
      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      release_info = data['args']['release_info']['redhat']
      begin
        result = @orchestrator.download_release(reporter, data['args']['task_uuid'], release_info)
      rescue Timeout::Error
        msg = "Timeout of release download is exceeded."
        Naily.logger.error msg
        reporter.report({'status' => 'error', 'error' => msg})
        return
      end
    end

    def check_redhat_credentials(data)
      credentials = data['args']['release_info']['redhat']
      task_id = data['args']['task_uuid']
      reporter = Naily::Reporter.new(@producer, data['respond_to'], task_id)
      @orchestrator.check_redhat_credentials(reporter, task_id, credentials)
    end

    def check_redhat_licenses(data)
      credentials = data['args']['release_info']['redhat']
      nodes = data['args']['nodes']
      task_id = data['args']['task_uuid']
      reporter = Naily::Reporter.new(@producer, data['respond_to'], task_id)
      @orchestrator.check_redhat_licenses(reporter, task_id, credentials, nodes)
    end

    def provision(data)
      Naily.logger.info("'provision' method called with data: #{data.inspect}")

      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      @orchestrator.fast_provision(reporter, data['args']['engine'], data['args']['nodes'])
    end

    def deploy(data)
      Naily.logger.info("'deploy' method called with data: #{data.inspect}")

      reporter = Naily::Reporter.new(@producer, data['respond_to'], data['args']['task_uuid'])
      @orchestrator.provision(reporter, data['args']['task_uuid'], data['args']['nodes'])

      begin
        result = @orchestrator.deploy(
          reporter, data['args']['task_uuid'], data['args']['nodes'], data['args']['attributes'])
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
