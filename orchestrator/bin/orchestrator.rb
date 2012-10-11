#!/usr/bin/env ruby
$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'orchestrator'

class DumbReporter
  def report(msg)
    p msg
  end
end

reporter = DumbReporter.new

nodes = [{'mac' => 'devnailgun.mirantis.com', 'role' => 'test_controller'}]
orchestrator = Orchestrator::Orchestrator.new
orchestrator.deploy(reporter, nodes)
