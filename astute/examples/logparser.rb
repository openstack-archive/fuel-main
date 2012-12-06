#!/usr/bin/env ruby

require 'rubygems'
require 'astute'



deploy_pattern_spec = {'type' => 'count-lines', 'separator' => 'lololo',
	'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
	'expected_line_number' => 500}
path='/var/tmp/1'
#n = Astute::LogParser.get_log_progress(path, pattern_spec)

path = '/home/adanin/anaconda.log'
pattern_spec = {'type' => 'pattern-list', 'chunk_size' =>  10000, # Size of block which reads for pattern searching.
'pattern_list' => [
  {'pattern' => 'Running kickstart %%pre script', 'progress' => 0.08},
  {'pattern' => 'to step enablefilesystems', 'progress' => 0.09},
  {'pattern' => 'to step reposetup', 'progress' => 0.13},
  {'pattern' => 'to step installpackages', 'progress' => 0.16},
  {'pattern' => 'Installing',
    'number' => 210, # Now it install 205 packets. Add 5 packets for growth in future.
    'p_min' => 0.16, # min percent
    'p_max' => 0.87 # max percent
    },
  # {'pattern' => 'to step postinstallconfig', 'progress' => 0.87},
  # {'pattern' => 'to step dopostaction', 'progress' => 0.92},
  ].reverse
}
#Astute::LogParser.add_log_separator(path)
#n = Astute::LogParser.get_log_progress(path, pattern_spec)

deployLogParser = Astute::LogParser::ParseNodeLogs.new('puppet-agent.log', deploy_pattern_spec)
nodes = [{'uid' => '1', 'ip' => '1.1.1.1'}]
n = deployLogParser.progress_calculate(nodes)
#deployLogParser.add_separator(nodes)

p n