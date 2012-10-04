#!/usr/bin/env ruby
$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'orchestrator'

nodes = ['nailgun']
metadata = {'role' => 'test_compute', 'meta' => 'some metadata'}
orchestrator = Orchestrator::Orchestrator.new(nodes, metadata)
orchestrator.deploy
