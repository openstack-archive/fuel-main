#!/usr/bin/env ruby
$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'naily'

nodes = ['admin']
metadata = {'role' => 'test_compute', 'meta' => 'some metadata'}
orchestrator = Naily::Orchestrator.new(nodes, metadata)
orchestrator.deploy
