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
        status = start_frame_listeners(JSON::parse(request[:iflist]))
        if status.empty?
          reply[:status] = true
        else
          reply[:status] = false
          reply[:errors] = status.to_json
        end
      end

      action "send_probing_frames" do
        validate :interfaces, String
        config_string = { "action" => "generate", "uid" => uid,
          "interfaces" => JSON::parse(request[:interfaces]) }.to_json
        #config_string = "{\"action\": \"generate\", \"uid\": \"#{uid}\", 
 #\"interfaces\": #{request[:interfaces]}}"
        send_probing_frames(config_string)
      end

      action "get_probing_info" do
        reply[:neigbours] = get_probing_frames(request[:iflist])
        reply[:uid] = uid
      end

      action "stop_frame_listeners" do
       status = stop_frame_listeners(JSON::parse(request[:iflist]))
        if status.empty?
          reply[:status] = true
        else
          reply[:status] = false
          reply[:errors] = status.to_json
        end
      end

      action "echo" do
        reply[:msg] = request[:msg]
        reply[:uid] = uid
      end

      action "vlan_split" do
        reply[:msg] = vlan_split(request[:msg])
      end

      private
      def vlan_split(s)
        s = s.split(',')
        ret = []
        s.each do |atom|
          l,r = atom.split('-', 2)
          if r.nil?
            if ret.index(l.to_i).nil?
              ret.push(l.to_i)
            end
          else
            for x in l.to_i.upto(r.to_i)
              if ret.index(x).nil?
                ret.push(x)
              end
            end
          end
        end
        return ret
      end

      def start_frame_listeners(iflist)
        errors = []
        out = ""
        err = ""
        iflist.each do |iface, vlans_string|
          vlans = vlan_split(vlans_string)
          vlans.each do |vlan|
            begin
              cmd = "vconfig add #{iface} #{vlan}"
              status = run(cmd, :stdout => out, :stderr => err)
              if status != 0
                raise("ERROR WHILE RUN COMMAND:\n#{cmd}\nSTDOUT:\n#{out}\nSTDERR:\n#{err}")
              end
              cmd = "ifconfig #{iface}.#{vlan} up"
              status = run(cmd, :stdout => out, :stderr => err)
              if status != 0
                raise("ERROR WHILE RUN COMMAND:\n#{cmd}\nSTDOUT:\n#{out}\nSTDERR:\n#{err}")
              end
              cmd = "net_probe.py -l #{iface}.#{vlan}"
              pid = fork { system(cmd) }
              Process.detach(pid)
            rescue Exception => e
              errors.push([iface, vlan, e.message])
            end
          end
        end
        return errors
      end

      def stop_frame_listeners(iflist)
        piddir = "/var/run/net_probe"
        pidfiles = Dir.glob(File.join(piddir, '*'))
        pidfiles.each do |f|
          begin
            Process.kill("INT", File.basename(f).to_i)
          rescue Errno::ESRCH
            File.unlink(f)
          end
        end
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
        errors = []
        out = ""
        err = ""
        iflist.each do |iface, vlans_string|
          vlans = vlan_split(vlans_string)
          vlans.each do |vlan|
            begin
              cmd = "ifconfig #{iface}.#{vlan} down"
              status = run(cmd, :stdout => out, :stderr => err)
              if status != 0
                raise("ERROR WHILE RUN COMMAND:\n#{cmd}\nSTDOUT:\n#{out}\nSTDERR:\n#{err}")
              end
              cmd = "vconfig rem #{iface}.#{vlan}"
              status = run(cmd, :stdout => out, :stderr => err)
              if status != 0
                raise("ERROR WHILE RUN COMMAND:\n#{cmd}\nSTDOUT:\n#{out}\nSTDERR:\n#{err}")
              end
            rescue Exception => e
              errors.push([iface, vlan, e.message])
            end
          end
        end
        return errors
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

      def get_probing_frames(iflist)
        stop_frame_listeners(iflist)
        neigbours = Hash.new
        pattern = "/var/tmp/net-probe-dump-*"
        Dir.glob(pattern).each do |file|
          data = ""
          open(file).readlines.each do |f|
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
