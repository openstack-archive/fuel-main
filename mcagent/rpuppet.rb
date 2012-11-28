$LOAD_PATH << File.join(File.dirname(__FILE__))  # So we can load rapply & node_indirector.rb from the same dir
require 'puppet/util/command_line'
require 'puppet/application'
require 'puppet'

load    'rapply.rb'  # Don't do require here: it requires Puppet.features, which is not available at this moment yet
require 'node_indirector'

module Astute
  def self.set_config(cfg)
    @config = cfg
  end

  # Node indirector calls this method to get configuration
  def self.get_config
    @config
  end
end

module MCollective
  module Agent
    class Rpuppet < RPC::Agent

      action "run" do
        # mco rpc rpuppet run data='{"environment": "production", "classes": {"nailytest::test_rpuppet": {"rpuppet": ["controller"]}}}' -v
        validate :data, String
        config = JSON.parse(request[:data])
        Log.info("Received configuration: #{config.inspect}")
        Astute.set_config(config)

        # /dev/null instead of empty site.pp required by puppet run
        cmdline = Puppet::Util::CommandLine.new("puppet", ["apply", "/dev/null", "--modulepath=/opt/fuel", "--debug", "--logdest=/var/log/puppetrun.log", "--node_terminus=exec"])
        Puppet.settings.initialize_global_settings(cmdline.args) unless Puppet.settings.global_defaults_initialized?

        app = Puppet::Application::Rapply.new(cmdline)

        # TODO: what are these plugins for ??
        #Puppet::Plugins.on_application_initialization(:application_object => self)
        Log.info("Running puppet...")
        app.run
      end
    end
  end
end
