require "json"
require "tempfile"
require "socket"
require "timeout"

module MCollective
  module Agent
    class Net_probe<RPC::Agent
      def startup_hook
        @pattern = "/var/tmp/net-probe-dump*"
      end

      action "start_frame_listeners" do
        start_frame_listeners
      end

      action "send_probing_frames" do
        send_probing_frames
      end

      action "get_probing_info" do
        get_probing_info
      end

      action "stop_frame_listeners" do
        stop_frame_listeners
      end

      private

      def get_uid
        File.open('/etc/nailgun_uid') do |fo|
          uid = fo.gets.chomp
          return uid
        end
      end

      def start_frame_listeners
        validate :interfaces, String
        config = {
          "action" => "listen",
          "interfaces" => JSON.parse(request[:interfaces]),
          "dump_file" => "/var/tmp/net-probe-dump",
          "ready_address" => "localhost",
          "ready_port" => 31338,
        }

        if request.data.key?('config')
          config.merge!(JSON.parse(request[:config]))
        end

        # we want to be sure that there is no frame listeners running
        stop_frame_listeners

        # wipe out old stuff before start
        Dir.glob(@pattern).each do |file|
          File.delete file
        end

        f = Tempfile.new "net_probe"
        f.write config.to_json
        fpath = f.path
        f.close

        begin
          socket = Socket.new( Socket::AF_INET, Socket::SOCK_STREAM, 0)
          sockaddr = Socket.pack_sockaddr_in(config['ready_port'], config['ready_address'])
          socket.bind(sockaddr)
          socket.listen(1)
        rescue Exception => e
          reply.fail "Socket error: #{e.to_s}"
        else

          cmd = "net_probe.py -c #{fpath}"
          pid = fork { `#{cmd}` }
          Process.detach(pid)

          # It raises Errno::ESRCH if there is no process, so we check that it runs
          sleep 1
          begin
            Process.kill(0, pid)
          rescue Errno::ESRCH => e
            reply.fail "Failed to run '#{cmd}'"
          else
            begin
              Timeout::timeout(120) do
                client, clientaddr = socket.accept
                status = client.read
                reply.fail "Wrong listener status: '#{status}'" unless status =~ /READY/
                client.close
              end
            rescue Timeout::Error
              reply.fail "Listener did not reported status."
            end
          end
        ensure
          socket.shutdown
          socket.close
        end
      end

      def send_probing_frames
        validate :interfaces, String
        config = { "action" => "generate", "uid" => get_uid,
                   "interfaces" => JSON.parse(request[:interfaces]) }
        if request.data.key?('config')
          config.merge!(JSON.parse(request[:config]))
        end
        cmd = "net_probe.py -c -"
        status = run(cmd, :stdin => config.to_json, :stdout => :out, :stderr => :error)
        reply.fail "Failed to send probing frames, cmd='#{cmd}' failed, config: #{config.inspect}" if status != 0
      end

      def get_probing_info
        stop_frame_listeners
        neighbours = Hash.new
        Dir.glob(@pattern).each do |file|
          p = JSON.load(File.read(file))
          neighbours.merge!(p)
        end
        reply[:neighbours] = neighbours
        reply[:uid] = get_uid
      end

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
