#!/usr/bin/env ruby
$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'orchestrator'

nodes = [{'mac' => 'nailgun', 'role' => 'test_controller'}]
orchestrator = Orchestrator::Orchestrator.new
orchestrator.deploy(nodes)
