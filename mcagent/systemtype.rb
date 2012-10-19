module MCollective
  module Agent
    class Systemtype < RPC::Agent
      file = "/etc/nailgun_systemtype"

      action "get_type" do
        begin
          reply[:node_type] = File.read(file)
        rescue
          reply.fail! $!.to_s
        end
      end
    end
  end
end
