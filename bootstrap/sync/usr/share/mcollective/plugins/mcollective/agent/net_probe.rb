require "json"

module MCollective
  module Agent
    class Net_probe<RPC::Agent
      metadata    :name        => "Network Probe Agent",
                  :description => "Check network connectivity between nodes.",
                  :author      => "Andrey Danin",
                  :license     => "MIT",
                  :version     => "0.1",
                  :url         => "http://mirantis.com",
                  :timeout     => 60

      uid = open('/etc/bootif').gets.chomp

      action "start_frame_listeners" do
        validate :iflist, String
        status = start_frame_listeners(JSON.parse(request[:iflist]))
        if status.empty?
          reply[:status] = true
        else
          reply[:status] = false
          reply[:errors] = status.to_json
        end
      end

      action "send_probing_frames" do
        validate :interfaces, String
        config = { "action" => "generate", "uid" => uid,
          "interfaces" => JSON.parse(request[:interfaces]) }
        if request.data.key?('config')
          config.merge!(JSON.parse(request[:config]))
        end
        send_probing_frames(config)
      end

      action "get_probing_info" do
        reply[:neigbours] = get_probing_frames
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

      def start_frame_listeners(iflist)
        errors = []
        iflist.each do |iface|
          begin
            cmd = "net_probe.py -l #{iface}"
            pid = fork { system(cmd) }
            Process.detach(pid)
          rescue Exception => e
            errors.push("Error occured while running command \"#{cmd}\": #{e.message}")
          end
        end
        return errors
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

      def send_probing_frames(config)
        cmd = "net_probe.py -"
        out = ""
        err = ""
        status = run(cmd, :stdin => config.to_json, :stdout => out, :stderr => err)
        reply[:stdout] = out
        reply[:stderr] = err
        if status == 0:
          reply[:status] = true
        else
          reply[:status] = false
        end
      end

      def get_probing_frames
        stop_frame_listeners
        neigbours = Hash.new
        pattern = "/var/tmp/net-probe-dump-*"
        Dir.glob(pattern).each do |file|
          data = ""
          open(file).readlines.each do |f|
            data += f
          end
          p = JSON.load(data)
          neigbours.merge!(p)
        end
        return neigbours
      end
    end
  end
end

# vi:tabstop=2:expandtab:ai:filetype=ruby
