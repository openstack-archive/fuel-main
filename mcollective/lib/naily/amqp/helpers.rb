require 'logger'

module Naily
  module Amqp
    module Helpers

      def logger
        logger = ::Logger.new(STDOUT)
        logger.level = ::Logger::DEBUG
        logger
      end
  
      def random_string(length=16, downcase=true)
        chars = ('a'..'z').to_a + ('A'..'Z').to_a + ('0'..'9').to_a
        rnd = ""
        length.times do |i| 
          rnd << chars[rand(chars.length)] 
        end
        rnd.downcase! if downcase
        rnd
      end
      
    end
  end
end
