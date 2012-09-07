module MCollective
  module Agent
    class Naily < RPC::Agent
      metadata \
      :name        => "Naily Agent",
      :description => "Naily Agent",
      :author      => "Mirantis Inc.",
      :license     => "Apache License 2.0",
      :version     => "0.0.1",
      :url         => "http://mirantis.com",
      :timeout     => 300

      def startup_hook
        @lockfile = @config.pluginconf["naily.lockfile"] || 
          "/var/lock/naily.lock"
        @puppet = @config.pluginconf["naily.puppet"] ||
          "/usr/bin/puppet"
        @puppetlog = @config.pluginconf["naily.puppetlog"] ||
          "/var/log/puppet.log"
        @puppetmodules = @config.pluginconf["naily.puppetmodules"] ||
          "/etc/puppet/modules"
        @sitepp = @config.pluginconf["naily.sitepp"] ||
          "/etc/puppet/manifests/site.pp"
      end

      action "runonce" do
        runonce
      end

      action "echo" do
        validate :msg, String
        reply[:msg] = "Hello, it is my reply: #{request[:msg]}"
      end

      private
     
      def running?
        status = run("flock -w 0 -o #{@lockfile} -c ''", :cwd => "/")
        return true if status != 0
        return false
      end

      def runonce
        if running?
          reply.fail "Agent is running at the moment"
        else
          runonce_background
        end
      end

      def flock_command command
        return "flock -w 0 -o #{@lockfile} -c \"#{command}\""
      end

      def runonce_background
        
        cmd = [@puppet, "apply"]
        cmd << ["-l", @puppetlog]
        cmd << "--verbose"
        cmd << "--debug"
        cmd << ["--modulepath", @puppetmodules]
        cmd << @sitepp
        cmd = cmd.join(" ")

        cmd = flock_command cmd

        reply[:command] = cmd
        reply[:status] = run(
                             cmd, 
                             :stdout => :output, 
                             :stderr => :err, 
                             :chomp => true
                             )

      end

    end
  end
end
