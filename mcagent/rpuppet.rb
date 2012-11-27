$LOAD_PATH << File.join(File.dirname(__FILE__))
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
        validate :data, String
        config = JSON.parse(request[:data])
        Log.info("Received configuration: #{config.inspect}")
        Astute.set_config(config)

        `echo > /opt/site.pp`
        cmdline = Puppet::Util::CommandLine.new("puppet", ["apply", "/opt/site.pp", "--modulepath=/opt/fuel", "--debug", "--logdest=/var/log/puppetrun.log"])
        Puppet.settings.initialize_global_settings(cmdline.args) unless Puppet.settings.global_defaults_initialized?

        app = Puppet::Application::Rapply.new(cmdline)

        # TODO: what are these plugins for ??
        #Puppet::Plugins.on_application_initialization(:application_object => self)
        app.run
      end
    end
  end
end
