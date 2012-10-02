require "json"
require "base64"

module MCollective
  module Agent
    class Erase_node<RPC::Agent
      metadata    :name        => "Erase node bootloader",
                  :description => "Erase node bootloader and reboot it.",
                  :author      => "Andrey Danin",
                  :license     => "MIT",
                  :version     => "0.1",
                  :url         => "http://mirantis.com",
                  :timeout     => 60

      action "erase_node" do
        validate :dev, String
        if File.exist?(request[:dev])
          begin
            header = open(request[:dev]).sysread(512)
            dev = open(request[:dev], 'w')
            dev.syswrite("\000"*512)
            dev.close
            reply[:status] = true
          rescue Exception => e
            reply[:status] = false
            reply[:error] = e.message
          ensure
            reply[:header] = Base64.encode64(header)
          end
        else
          reply[:status] = false
          reply[:error] = "File \"#{request[:dev]}\" not exist."
        end
      end

      action "reboot_node" do
        out = ""
        err = ""
        cmd = "shutdown -r 5"
        status = run(cmd, :stdout => out, :stderr => err)
        if status != 0
          reply[:errors] = "ERROR WHILE RUN COMMAND:\n#{cmd}\nSTDOUT:\n#{out}\nSTDERR:\n#{err}"
        end
        reply[:status] = status
      end


    end
  end
end
# vi:tabstop=2:expandtab:ai:filetype=ruby