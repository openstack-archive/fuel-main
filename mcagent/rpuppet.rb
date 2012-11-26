require 'singleton'
require 'puppet/util/command_line'
require 'puppet/application'
require 'puppet'
load    '/vagrant/mcagent/rapply.rb'  # Don't do require here: it requires Puppet.features, which is not available at this moment yet
require '/vagrant/mcagent/node_indirector.rb'

module Astute
  def self.set_config(cfg)
    @config = cfg
  end

  def self.get_config
    @config
  end
end

module MCollective
  module Agent
    class Rpuppet < RPC::Agent

      action "run" do
        cmdline = Puppet::Util::CommandLine.new("puppet", ["apply", "/root/site.pp", "--modulepath=/vagrant/puppet", "--debug", "--logdest=/tmp/puppetlog"])
        Puppet.settings.initialize_global_settings(cmdline.args) unless Puppet.settings.global_defaults_initialized?
        #validate :data, String
        Astute.set_config({"environment"=>"production", "parameters"=>nil, "classes"=>{"nailytest"=>{"role"=>["controller"]}}})

        app = Puppet::Application::Rapply.new(cmdline)

        # TODO: what are these plugins for ??
        #Puppet::Plugins.on_application_initialization(:application_object => self)
        app.run
      end
    end
  end
end
