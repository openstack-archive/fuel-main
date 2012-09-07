module MCollective
  module Agent
    class Fake < RPC::Agent

      action "echo" do
        validate :msg, String
        reply[:msg] = "Hello, it is my reply: #{request[:msg]}"
      end

    end
  end
end
