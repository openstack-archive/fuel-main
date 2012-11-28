# NOTE(mihgen): this file is modified copy of puppet's lib/puppet/application/apply.rb
require 'yaml'

require 'puppet/application'
require 'puppet/configurer'
require 'puppet/node'

class Puppet::Application::Rapply < Puppet::Application
  option("--debug","-d")
  option("--logdest LOGDEST", "-l") do |arg|
    begin
      Puppet::Util::Log.newdestination(arg)
      options[:logset] = true
    rescue => detail
      $stderr.puts detail.to_s
    end
  end

  def main
    manifest = command_line.args.shift
    raise "Could not find file #{manifest}" unless ::File.exist?(manifest)
    Puppet.warning("Only one file can be applied per run. 
                   Skipping #{command_line.args.join(', ')}") if command_line.args.size > 0
    Puppet[:manifest] = manifest

    unless Puppet[:node_name_fact].empty?
      # Collect our facts.
      unless facts = Puppet::Node::Facts.indirection.find(Puppet[:node_name_value])
        raise "Could not find facts for #{Puppet[:node_name_value]}"
      end

      Puppet[:node_name_value] = facts.values[Puppet[:node_name_fact]]
      facts.name = Puppet[:node_name_value]
    end

    # Find our Node. It's expected it will look for it in our terminus (node_indirector.rb)
    unless node = Puppet::Node.indirection.find(Puppet[:node_name_value])
      raise "Could not find node #{Puppet[:node_name_value]}"
    end

    # Merge in the facts.
    node.merge(facts.values) if facts

    # Allow users to load the classes that puppet agent creates.
    if options[:loadclasses]
      file = Puppet[:classfile]
      if FileTest.exists?(file)
        raise "#{file} is not readable" unless FileTest.readable?(file)
        node.classes = ::File.read(file).split(/[\s\n]+/)
      end
    end

    begin
      # Compile our catalog
      starttime = Time.now
      catalog = Puppet::Resource::Catalog.indirection.find(node.name, :use_node => node)

      # Translate it to a RAL catalog
      catalog = catalog.to_ral

      catalog.finalize

      catalog.retrieval_duration = Time.now - starttime

      configurer = Puppet::Configurer.new
      exit_status = configurer.run(:catalog => catalog, :pluginsync => false)

      raise "exit status = #{exit_status}" if exit_status != 0
    rescue => detail
      Puppet.log_exception(detail)
      raise detail.message
    end
  end

  def setup
    Puppet::Util::Log.newdestination(:console) unless options[:logset]
    client = nil
    server = nil

    Puppet::Transaction::Report.indirection.cache_class = :yaml

    if options[:debug]
      Puppet::Util::Log.level = :debug
    elsif options[:verbose]
      Puppet::Util::Log.level = :info
    end
  end
end
