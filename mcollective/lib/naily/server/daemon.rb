require 'logger'
require 'eventmachine'
require 'naily/amqp/driver'

module Naily
  module Server
    class Daemon
      def initialize
        @logger = Logger.new(STDOUT)
        @logger.level = Logger::DEBUG

        @options = {
          :host => Config.amqp_host,
          :port => Config.amqp_port,
          :username => Config.amqp_username,
          :password => Config.amqp_password,
          
          :topic_exchange_name => Config.topic_exchange_name,
          :topic_queue_name => Config.topic_queue_name,
          :topic_queue_routing_key => Config.topic_queue_routing_key
        }
      end

      def run
        EM.run do
          driver = Naily::Amqp::Driver.new @options
          
          Signal.trap("INT") do
            @logger.debug("INT signal has been caught")
            driver.disconnect do
              EventMachine.stop 
            end
          end
        end
      end
    end
  end
end
