require "json"
require "base64"

module MCollective
  module Agent
    class Erase_node<RPC::Agent
      action "erase_node" do
        validate :file, String
        if File.exist?(request[:file])
          if request.data.key?(:get_data) and request.data[:get_data] != ''
            header = get_data(request[:file], 512)
            reply[:erased_data] = Base64.encode64(header)
          end
          request_reboot = request.data.key?(:reboot) and request.data[:reboot] != ''
          if request.data.key?(:dry_run) and request.data[:dry_run] != ''
            reply[:status] = true
            reply[:dry_run] = true
            if request_reboot
              reply[:reboot] = true
            end
          else
            begin
              erase_data(request[:file], 512)
              reply[:status] = true
              if request_reboot
                reboot
                reply[:reboot] = true
              end
            rescue Exception => e
              reply[:status] = false
              reply[:error_msg] = e.message
            end
          end
        else
          reply[:status] = false
          reply[:error_msg] = "File \"#{request[:file]}\" not exist."
        end
      end

      action "reboot_node" do
        reboot
      end

      private

      def reboot
        cmd = "/bin/sleep 5; /sbin/shutdown -r"
        pid = fork { system(cmd) }
        Process.detach(pid)
      end

      def get_data(file, length, offset=0)
        fd = open(file)
        fd.seek(offset)
        ret = fd.sysread(length)
        fd.close
        return ret
      end

      def erase_data(file, length, offset=0)
        fd = open(file, 'w')
        fd.seek(offset)
        ret = fd.syswrite("\000"*length)
        fd.close
      end

    end
  end
end
# vi:tabstop=2:expandtab:ai:filetype=ruby
