module MCollective
  module Agent
    # An agent to manage the Puppet Daemon
    #
    # Configuration Options:
    #    puppetd.splaytime - Number of seconds within which to splay; no splay
    #                        by default
    #    puppetd.statefile - Where to find the state.yaml file; defaults to
    #                        /var/lib/puppet/state/state.yaml
    #    puppetd.lockfile  - Where to find the lock file; defaults to
    #                        /var/lib/puppet/state/puppetdlock
    #    puppetd.puppetd   - Where to find the puppet agent binary; defaults to
    #                        /usr/bin/puppet agent
    #    puppetd.summary   - Where to find the summary file written by Puppet
    #                        2.6.8 and newer; defaults to
    #                        /var/lib/puppet/state/last_run_summary.yaml
    #    puppetd.pidfile   - Where to find puppet agent's pid file; defaults to
    #                        /var/run/puppet/agent.pid
    class Puppetd<RPC::Agent
      def startup_hook
        @splaytime = @config.pluginconf["puppetd.splaytime"].to_i || 0
        @lockfile = @config.pluginconf["puppetd.lockfile"] || "/var/lib/puppet/state/puppetdlock"
        @statefile = @config.pluginconf["puppetd.statefile"] || "/var/lib/puppet/state/state.yaml"
        @pidfile = @config.pluginconf["puppet.pidfile"] || "/var/run/puppet/agent.pid"
        @puppetd = @config.pluginconf["puppetd.puppetd"] || "/usr/bin/puppet agent"
        @last_summary = @config.pluginconf["puppet.summary"] || "/var/lib/puppet/state/last_run_summary.yaml"
      end

      action "last_run_summary" do
        last_run_summary
        set_status
      end

      action "enable" do
        enable
      end

      action "disable" do
        disable
      end

      action "runonce" do
        runonce
      end

      action "status" do
        set_status
      end

      private
      def last_run_summary
        # wrap into begin..rescue: fixes PRD-252
        begin
          summary = YAML.load_file(@last_summary)
        rescue
          summary = {}
        end

        # It should be empty hash, if 'resources' key is not defined, because otherwise merge will fail with TypeError
        summary["resources"] ||= {}
        # Astute relies on last_run, so we must set last_run
        summary["time"] ||= {}
        summary["time"]["last_run"] ||= 0
        # if 'failed' is not provided, it means something is wrong. So default value is 1.
        reply[:resources] = {"failed"=>1, "changed"=>0, "total"=>0, "restarted"=>0, "out_of_sync"=>0}.merge(summary["resources"])

        ["time", "events", "changes", "version"].each do |dat|
          reply[dat.to_sym] = summary[dat]
        end
      end

      def set_status
        reply[:status]  = puppet_daemon_status
        reply[:running] = reply[:status] == 'running'  ? 1 : 0
        reply[:enabled] = reply[:status] == 'disabled' ? 0 : 1
        reply[:idling]  = reply[:status] == 'idling'   ? 1 : 0
        reply[:stopped] = reply[:status] == 'stopped'  ? 1 : 0
        reply[:lastrun] = 0
        reply[:lastrun] = File.stat(@statefile).mtime.to_i if File.exists?(@statefile)
        reply[:runtime] = Time.now.to_i - reply[:lastrun]
        reply[:output]  = "Currently #{reply[:status]}; last completed run #{reply[:runtime]} seconds ago"
      end

      def puppet_daemon_status
        locked = File.exists?(@lockfile)
        disabled = locked && File::Stat.new(@lockfile).zero?
        has_pid = File.exists?(@pidfile)

        return 'disabled' if disabled
        return 'running'  if   locked && has_pid
        return 'idling'   if ! locked && has_pid
        return 'stopped'  if ! has_pid
      end

      def runonce
        set_status
        case (reply[:status])
        when 'disabled' then     # can't run
          reply.fail "Empty Lock file exists; puppet agent is disabled."

        when 'running' then      # can't run two simultaniously
          reply.fail "Lock file and PID file exist; puppet agent is running."

        when 'idling' then       # signal daemon
          pid = File.read(@pidfile)
          if pid !~ /^\d+$/
            reply.fail "PID file does not contain a PID; got #{pid.inspect}"
          else
            begin
              ::Process.kill(0, Integer(pid)) # check that pid is alive
              # REVISIT: Should we add an extra round of security here, and
              # ensure that the PID file is securely owned, or that the target
              # process looks like Puppet?  Otherwise a malicious user could
              # theoretically signal arbitrary processes with this...
              begin
                ::Process.kill("USR1", Integer(pid))
                reply[:output] = "Signalled daemonized puppet agent to run (process #{Integer(pid)}); " + (reply[:output] || '')
              rescue Exception => e
                reply.fail "Failed to signal the puppet agent daemon (process #{pid}): #{e}"
              end
            rescue Errno::ESRCH => e
              # PID is invalid, run puppet onetime as usual
              runonce_background
            end
          end

        when 'stopped' then      # just run
          runonce_background

        else
          reply.fail "Unknown puppet agent status: #{reply[:status]}"
        end
      end

      def runonce_background
        cmd = [@puppetd, "--onetime", "--logdest", 'syslog']

        unless request[:forcerun]
          if @splaytime && @splaytime > 0
            cmd << "--splaylimit" << @splaytime << "--splay"
          end
        end

        cmd = cmd.join(" ")

        output = reply[:output] || ''
        run(cmd, :stdout => :output, :chomp => true)
        reply[:output] = "Called #{cmd}, " + output + (reply[:output] || '')
      end

      def enable
        if File.exists?(@lockfile)
          stat = File::Stat.new(@lockfile)

          if stat.zero?
            File.unlink(@lockfile)
            reply[:output] = "Lock removed"
          else
            reply[:output] = "Currently running; can't remove lock"
          end
        else
          reply.fail "Already enabled"
        end
      end

      def disable
        if File.exists?(@lockfile)
          stat = File::Stat.new(@lockfile)

          stat.zero? ? reply.fail("Already disabled") : reply.fail("Currently running; can't remove lock")
        else
          begin
            File.open(@lockfile, "w") { |file| }

            reply[:output] = "Lock created"
          rescue Exception => e
            reply.fail "Could not create lock: #{e}"
          end
        end
      end
    end
  end
end

# vi:tabstop=2:expandtab:ai:filetype=ruby
