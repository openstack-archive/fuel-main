#!/usr/bin/env ruby

$LOAD_PATH.unshift(File.expand_path(File.join(File.dirname(__FILE__), "..", "lib")))

require 'naily/mcclient/simple'

client = Naily::MCClient::Simple.new
client.run
