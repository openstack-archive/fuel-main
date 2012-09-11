#!/usr/bin/env ruby

$LOAD_PATH.unshift(File.expand_path(File.join(File.dirname(__FILE__), "..", "lib")))

require 'rubygems'
require 'naily/server/config'
require 'naily/server/daemon'

Naily::Server::Config.define do |config|
  config.driver = :amqp
  config.amqp_host = "127.0.0.1"
  config.amqp_port = 5672
  config.amqp_username = "guest"
  config.amqp_password = "guest"
  config.topic_exchange_name = "nailgun"
  config.topic_queue_name = "mcollective"
  config.topic_queue_routing_key = "mcollective"
end


daemon = Naily::Server::Daemon.new
daemon.run
  

