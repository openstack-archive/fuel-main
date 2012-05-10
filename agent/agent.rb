#!/usr/bin/env ruby

require 'rubygems'

require 'ohai'
require 'httpclient'
require 'json'

URL = "http://localhost:4567/test"

ohai = ::Ohai::System.new
ohai.require_plugin("network")
ohai.require_plugin("linux::network")
ohai.require_plugin("linux::cpu")
ohai.require_plugin("linux::hostname")
ohai.require_plugin("linux::memory")
ohai.require_plugin("linux::block_device")

# We can fetch some values by defining set keys like this:
#mac, ip, network = ohai.data.values_at("macaddress", "ipaddress", "network")

cli = HTTPClient.new
cli.post(URL, ohai.data.to_json)
