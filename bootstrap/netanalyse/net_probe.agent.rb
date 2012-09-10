module MCollective
  module Agent
    require "json"
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
    #                        /usr/sbin/puppetd
    #    puppetd.summary   - Where to find the summary file written by Puppet
    #                        2.6.8 and newer; defaults to
    #                        /var/lib/puppet/state/last_run_summary.yaml
    #    puppetd.pidfile   - Where to find puppet agent's pid file; defaults to
    #                        /var/run/puppet/agent.pid
    class NetProbe<RPC::Agent
      metadata    :name        => "Network Probe Agent",
                  :description => "Check network connectivity between nodes.",
                  :author      => "Andrey Danin",
                  :license     => "MIT",
                  :version     => "0.1",
                  :timeout     => 60

      action "start_frame_listeners" do
        input :iflist,
               :prompt      => "List of interfaces",
               :description => "List of interface names to start listen frames on it",
               :type        => :string,
               :validation  => '^([a-zA-Z]+\d*])(,[a-zA-Z]+\d*])*$',
               :optional    => false
        validate :iflist, String
        status, msg = start_frame_listeners(iflist.split(","))
        reply[:status] = status
        if not status
          reply[:msg] = msg
        end
      end

      action "send_probing_frames" do
         input :config,
               :prompt      => "",
               :description => "",
               :type        => :string,
               :optional    => false
        validate :iflist, String
        send_probing_frames(:config)
      end

      action "get_probing_info" do
        status, msg = get_probing_info
      end

      private
      def start_frame_listeners(iflist)
        begin
          iflist.each do |iface|
            cmd = "sudo tcpdump -i #{iface} -Z adanin -w /var/tmp/dump-#{iface}.pcap udp port"
            pid = fork { system(cmd) }
            Process.detach(pid)
          end
          return true
        rescue
          return false, "#{$!}"
        end
      end

      def stop_frame_listeners()
        system("killall tcpdump")
      end

      def send_probing_frames(config_string)
        config = JSON.load(config_string)
        cmd = "sudo python /var/tmp/net_probe.py"
        out = ""
        err = ""
        status = run(cmd, :stdin => JSON.dump(config), :stdout => out, :stderr => err)
        if status == 0:
          reply[:status] = true
        else
          reply[:status] = false
          reply[:msg] = out + err
        end
      end

      def get_probing_info()
        stop_frame_listeners
        file_list = "/var/tmp/dump-*.pcap"
        out = ""
        err = ""
        file_list.each do |file|
          cmd = "tcpdump -f #{file}"
          status = run(cmd, :stdout => out, :stderr => err)
        end
      end
    end
  end
end

# vi:tabstop=2:expandtab:ai:filetype=ruby
