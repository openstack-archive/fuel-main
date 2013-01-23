#!/usr/bin/env ruby

require 'rubygems'
require 'astute'
require 'tempfile'
require 'date'



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

#deployLogParser = Astute::LogParser::ParseNodeLogs.new('puppet-agent.log', deploy_pattern_spec)
#nodes = [{'uid' => '1', 'ip' => '1.1.1.1'}]
#n = deployLogParser.progress_calculate(nodes)
#deployLogParser.add_separator(nodes)


def test_supposed_time_parser(pattern_spec)
  sec = 1.0 /24 / 3600
  fo = Tempfile.new('logparse')
  path = fo.path
  n = Astute::LogParser.get_log_progress(path, pattern_spec)
  p "Initial progress: #{n}"
  log_delta = sec * rand(20)

  pattern_spec['pattern_list'].dup.reverse.each do |pattern|
    prev_delta = log_delta
    log_delta = sec * rand(20)
    log_date = DateTime.now() - log_delta
    pattern_spec['_nodes'][path]['_prev_time'] = log_date - prev_delta - sec
    fo.write("#{log_date.strftime(pattern_spec['date_format'])} #{pattern['pattern']}\n")
    fo.flush
    n = Astute::LogParser.get_log_progress(path, pattern_spec)
    p "Progress: #{n}"
  end
  fo.close!
end

def test_component_parser(pattern_spec)
  fo = Tempfile.new('logparse')
  path = fo.path
  progress = Astute::LogParser.get_log_progress(path, pattern_spec)
  p "Initial progress: #{progress}"
  while progress < 1
    component = pattern_spec['components_list'][ rand(pattern_spec['components_list'].length) ]
    pattern = component['patterns'][ rand(component['patterns'].length) ]
    fo.write("#{pattern['pattern']}\n")
    fo.flush
    progress = Astute::LogParser.get_log_progress(path, pattern_spec)
    p "Progress: #{progress}"
  end
  fo.close!
end



pattern_spec = {'type' => 'supposed-time',
  'chunk_size' => 10000,
  'date_format' => '%Y-%m-%dT%H:%M:%S',
  'date_regexp' => '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
  'pattern_list' => [
    {'pattern' => 'to step installpackages', 'supposed_time' => 10},
    {'pattern' => 'pattern_2', 'supposed_time' => 10},
    {'pattern' => 'pattern_3', 'supposed_time' => 10},
    {'pattern' => 'pattern_4', 'supposed_time' => 10},
    {'pattern' => 'pattern_5', 'supposed_time' => 10},
    {'pattern' => 'pattern_6', 'supposed_time' => 10},
    ].reverse,
  }

[1,2].each {|n| test_supposed_time_parser(pattern_spec) }

pattern_spec = Astute::LogParser.get_default_pattern('puppet-log-components-list')
test_component_parser(pattern_spec)