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

      uid = ""
      open('/etc/bootif') do |f|
        uid = f.gets
      end

      action "start_frame_listeners" do
        validate :iflist, String
        status, msg = start_frame_listeners(request[:iflist].split(","))
        reply[:status] = status
        if not status
          reply[:msg] = msg
        end
      end

      action "send_probing_frames" do
        validate :interfaces, String
        config_string = "{\"action\": \"generate\", \"uid\": \"#{uid}\", 
 \"interfaces\": #{request[:interfaces]}}"
        send_probing_frames(config_string)
      end

      action "get_probing_info" do
        reply[:neigbours] = get_probing_frames
        reply[:uid] = uid
      end

      action "echo" do
        reply[:msg] = request[:msg]
        reply[:uid] = uid
      end

      private
      def start_frame_listeners(iflist)
        begin
          iflist.each do |iface|
            cmd = "net_probe.py -l #{iface}"
            pid = fork { system(cmd) }
            Process.detach(pid)
          end
          return true
        rescue
          return false, "#{$!}"
        end
      end

      def stop_frame_listeners()
        piddir = "/var/run/net_probe"
        pidfiles = Dir.glob(File.join(piddir, '*'))
        pidfiles.each do |f|
          #run("kill -INT #{File.basename(f)}")
          Process.kill("INT", File.basename(f))
        end
        while not pidfiles.empty? do
          pidfiles.each do |f|
            begin
              Process.getpgid(File.basename(f))
              File.unlink(f)
            rescue Errno::ESRCH, Errno::ENOENT
            end
          end
          pidfiles = Dir.glob(File.join(piddir, '*'))
        end
      end

      def send_probing_frames(config_string)
        config = JSON.load(config_string)
        cmd = "net_probe.py -"
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

      def get_probing_frames()
        stop_frame_listeners
        neigbours = Hash.new
        pattern = "/var/tmp/net-probe-dump-*"
        Dir.glob(pattern).each do |file|
          data = ""
          open(file) do |f|
            data += f.gets
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
