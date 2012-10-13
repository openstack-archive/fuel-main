require "json"

module MCollective
  module Agent
    class Net_probe<RPC::Agent

      uid = open('/etc/bootif').gets.chomp
      pattern = "/var/tmp/net-probe-dump-*"

      action "start_frame_listeners" do
        validate :iflist, String
        # wipe out old stuff before start
        Dir.glob(pattern).each do |file|
          File.delete file
        end
        iflist = JSON.parse(request[:iflist])
        iflist.each do |iface|
          cmd = "net_probe.py -l #{iface}"
          pid = fork { `#{cmd}` }
          Process.detach(pid)
          # It raises Errno::ESRCH if there is no process, so we check that it runs
          sleep 1
          begin
            Process.kill(0, pid)
          rescue Errno::ESRCH => e
            reply.fail "Failed to run '#{cmd}'"
          end
        end
      end

      action "send_probing_frames" do
        validate :interfaces, String
        config = { "action" => "generate", "uid" => uid,
                   "interfaces" => JSON.parse(request[:interfaces]) }
        if request.data.key?('config')
          config.merge!(JSON.parse(request[:config]))
        end
        cmd = "net_probe.py -"
        status = run(cmd, :stdin => config.to_json, :stdout => :out, :stderr => :error)
        reply.fail "Failed to send probing frames, cmd='#{cmd}' failed, config: #{config.inspect}" if status != 0
      end

      action "get_probing_info" do
        stop_frame_listeners
        neigbours = Hash.new
        Dir.glob(pattern).each do |file|
          p = JSON.load(File.read(file))
          neigbours.merge!(p)
        end
        reply[:neigbours] = neigbours
        reply[:uid] = uid
      end

      action "stop_frame_listeners" do
        stop_frame_listeners
      end

      action "echo" do
        request.data.each do |key, value|
          reply[key] = value
        end
        reply[:uid] = uid
      end

      private

      def stop_frame_listeners
        piddir = "/var/run/net_probe"
        pidfiles = Dir.glob(File.join(piddir, '*'))
        # Send SIGINT to all PIDs in piddir.
        pidfiles.each do |f|
          begin
            Process.kill("INT", File.basename(f).to_i)
          rescue Errno::ESRCH
            # Unlink pidfile if no such process.
            File.unlink(f)
          end
        end
        # Wait while all processes dump data and exit.
        while not pidfiles.empty? do
          pidfiles.each do |f|
            begin
              Process.getpgid(File.basename(f).to_i)
            rescue Errno::ESRCH
              begin
                File.unlink(f)
              rescue Errno::ENOENT
              end
            end
          end
          pidfiles = Dir.glob(File.join(piddir, '*'))
        end
      end
    end
  end
end

# vi:tabstop=2:expandtab:ai:filetype=ruby
