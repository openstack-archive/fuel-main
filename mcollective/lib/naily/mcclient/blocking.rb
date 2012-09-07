require 'mcollective'
require 'naily/framework/client'

module Naily
  module MCClient
    class Blocking
      include MCollective::RPC
      include Naily::Framework::Client
  
      def initialize
        @mc = rpcclient('naily')
        @mc.verbose = true
      end
  
      def run
        responses = []
        @mc.echo(:msg => "Testing fake agent plugin: before sleep").each do |response|
          responses << "Response: from: #{response[:sender]} message: #{response[:data][:msg]}"
        end
        sleep 10
        @mc.echo(:msg => "Testing fake agent plugin: after sleep").each do |response|
          responses << "Response: from: #{response[:sender]} message: #{response[:data][:msg]}"
        end
      end
      
      def disconnect
        @mc.disconnect
      end
    end
  end
end
