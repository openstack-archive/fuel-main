#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")
require 'tempfile'
require 'tmpdir'
require 'date'

include Astute

describe LogParser do
  def get_statistics_variables(progress_table)
    # Calculate some statistics variables: expectancy, standart deviation and
    # correlation coefficient between real and ideal progress calculation.
    total_time = 0
    real_expectancy = 0
    real_sqr_expectancy = 0
    prev_event_date = nil
    progress_table.each do |el|
      date = el[:date]
      prev_event_date = date unless prev_event_date
      progress = el[:progress].to_f
      period = date - prev_event_date
      hours, mins, secs, frac = Date::day_fraction_to_time(period)
      period_in_sec = hours * 60 * 60 + mins * 60 + secs
      total_time += period_in_sec
      real_expectancy += period_in_sec * progress
      real_sqr_expectancy += period_in_sec * progress ** 2
      el[:time_delta] = period_in_sec
      prev_event_date = date
    end

    # Calculate standart deviation for real progress distibution.
    real_expectancy = real_expectancy.to_f / total_time
    real_sqr_expectancy = real_sqr_expectancy.to_f / total_time
    real_standart_deviation = Math.sqrt(real_sqr_expectancy - real_expectancy ** 2)

    # Calculate PCC (correlation coefficient).
    ideal_sqr_expectancy = 0
    ideal_expectancy = 0
    t = 0
    ideal_delta = 100.0 / total_time
    mixed_expectancy = 0
    progress_table.each do |el|
      t += el[:time_delta]
      ideal_progress = t * ideal_delta
      ideal_expectancy += ideal_progress * el[:time_delta]
      ideal_sqr_expectancy += ideal_progress ** 2 * el[:time_delta]
      el[:ideal_progress] = ideal_progress
      mixed_expectancy += el[:progress] * ideal_progress * el[:time_delta]
    end

    ideal_expectancy = ideal_expectancy / total_time
    ideal_sqr_expectancy = ideal_sqr_expectancy / total_time
    mixed_expectancy = mixed_expectancy / total_time
    ideal_standart_deviation = Math.sqrt(ideal_sqr_expectancy - ideal_expectancy ** 2)
    covariance = mixed_expectancy - ideal_expectancy * real_expectancy
    pcc = covariance / (ideal_standart_deviation * real_standart_deviation)

    statistics = {
      'real_expectancy' => real_expectancy,
      'real_sqr_expectancy' => real_sqr_expectancy,
      'real_standart_deviation' => real_standart_deviation,
      'ideal_expectancy' => ideal_expectancy,
      'ideal_sqr_expectancy' => ideal_sqr_expectancy,
      'ideal_standart_deviation' => ideal_standart_deviation,
      'mixed_expectancy' => mixed_expectancy,
      'covariance' => covariance,
      'pcc' => pcc,
      'total_time' => total_time,
    }

    return statistics
  end

  def get_next_line(fo, date_regexp, date_format)
    until fo.eof?
      line = fo.readline
      date_string = line.match(date_regexp)
      if date_string
        date = DateTime.strptime(date_string[0], date_format)
        return line, date
      end
    end
  end

  def get_next_lines_by_date(fo, now, date_regexp, date_format)
    lines = ''
    until fo.eof?
      pos = fo.pos
      line, date = get_next_line(fo, date_regexp, date_format)
      if date <= now
        lines += line
      else
        fo.pos = pos
        return lines
      end
    end
    return lines
  end

  context "Correlation coeff. (PCC) of Provisioning progress bar calculation" do
    def provision_parser_wrapper(node)
      uids = [node['uid']]
      nodes = [node]
      time_delta = 5.0/24/60/60
      log_delay = 6*time_delta

      deploy_parser = Astute::LogParser::ParseProvisionLogs.new
      pattern_spec = deploy_parser.pattern_spec
      date_regexp = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
      date_format = '%Y-%m-%dT%H:%M:%S'

      Dir.mktmpdir do |dir|
        # Create temp log files and structures.
        pattern_spec['path_prefix'] = "#{dir}/"
        path = "#{pattern_spec['path_prefix']}#{node['fqdn']}/#{pattern_spec['filename']}"
        Dir.mkdir(File.dirname(File.dirname(path)))
        Dir.mkdir(File.dirname(path))
        node['file'] = File.open(path, 'w')
        src_filename = File.join(File.dirname(__FILE__), "..", "example-logs", node['src_filename'])
        node['src'] = File.open(src_filename)
        line, date = get_next_line(node['src'], date_regexp, date_format)
        node['src'].pos = 0
        node['now'] = date - log_delay
        node['progress_table'] ||= []

        # End 'while' cycle if reach EOF at all src files.
        until node['src'].eof?
          # Copy logs line by line from example logfile to tempfile and collect progress for each step.
          lines, date = get_next_lines_by_date(node['src'], node['now'], date_regexp, date_format)
          node['file'].write(lines)
          node['file'].flush
          node['last_lines'] = lines

          DateTime.stubs(:now).returns(node['now'])
          node_progress = deploy_parser.progress_calculate(uids, nodes)[0]
          node['progress_table'] << {:date => node['now'], :progress => node_progress['progress']}
          node['now'] += time_delta
        end

        nodes.each do |node|
          node['statistics'] = get_statistics_variables(node['progress_table'])
        end
        # Clear temp files.
        node['file'].close
        File.unlink(node['file'].path)
        Dir.unlink(File.dirname(node['file'].path))
      end

      return node
    end

    it "should be greather than 0.96" do
      node = {'uid' => '1', 'ip' => '1.0.0.1', 'fqdn' => 'slave-1.domain.tld', 'role' => 'controller', 'src_filename' => 'anaconda.log_',
        'meta' => { 'disks' =>
          [
          {'name' => 'flash drive', 'removable' => true, 'size' => 1000},
          {'name' => 'sda', 'removable'=> false, 'size' => 32*1000*1000*1000},
          ]
        }
      }
      calculated_node = provision_parser_wrapper(node)
      calculated_node['statistics']['pcc'].should > 0.96
    end

    it "it must be updated at least 5 times" do
      # Otherwise progress bar has no meaning I guess...
      pending('Not yet implemented')
    end

  end
  context "Correlation coeff. (PCC) of Deploying progress bar calculation" do
    def deployment_parser_wrapper(cluster_type, nodes)
      uids = nodes.map{|n| n['uid']}

      deploy_parser = Astute::LogParser::ParseDeployLogs.new(cluster_type)
      pattern_spec = deploy_parser.pattern_spec
      date_regexp = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
      date_format = '%Y-%m-%dT%H:%M:%S'

      Dir.mktmpdir do |dir|
        # Create temp log files and structures.
        pattern_spec['path_prefix'] = "#{dir}/"
        nodes.each do |node|
          path = "#{pattern_spec['path_prefix']}#{node['fqdn']}/#{pattern_spec['filename']}"
          Dir.mkdir(File.dirname(path))
          node['file'] = File.open(path, 'w')
          src_filename = File.join(File.dirname(__FILE__), "..", "example-logs", node['src_filename'])
          node['src'] = File.open(src_filename)
          node['progress_table'] ||= []
        end

        # End 'while' cycle if reach EOF at all src files.
        while nodes.index{|n| not n['src'].eof?}
          # Copy logs line by line from example logfile to tempfile and collect progress for each step.
          nodes.each do |node|
            unless node['src'].eof?
              line = node['src'].readline
              node['file'].write(line)
              node['file'].flush
              node['last_line'] = line
            else
              node['last_line'] = ''
            end
          end

          nodes_progress = deploy_parser.progress_calculate(uids, nodes)
          nodes_progress.each do |progress|
            node = nodes.at(nodes.index{|n| n['uid'] == progress['uid']})
            date_string = node['last_line'].match(date_regexp)
            if date_string
              date = DateTime.strptime(date_string[0], date_format)
              node['progress_table'] << {:date => date, :progress => progress['progress']}
            end
          end
        end

        nodes.each do |node|
          node['statistics'] = get_statistics_variables(node['progress_table'])
        end
        # Clear temp files.
        nodes.each do |n|
          n['file'].close
          File.unlink(n['file'].path)
          Dir.unlink(File.dirname(n['file'].path))
        end
      end

      return nodes
    end

    it "should be greather than 0.85 for HA deployment" do
      nodes = [
        {'uid' => '1', 'ip' => '1.0.0.1', 'fqdn' => 'slave-1.domain.tld', 'role' => 'controller', 'src_filename' => 'puppet-agent.log.ha.contr.2'},
        {'uid' => '2', 'ip' => '1.0.0.2', 'fqdn' => 'slave-2.domain.tld', 'role' => 'compute', 'src_filename' => 'puppet-agent.log.ha.compute'},
      ]

      calculated_nodes = deployment_parser_wrapper('ha', nodes)
      calculated_nodes.each {|node| node['statistics']['pcc'].should > 0.85}

      # For debug purposes.
      # print "\n"
      # calculated_nodes.each do |node|
      #   print node['statistics'].inspect, "\n", node['statistics']['pcc'], "\n", node['progress_table'][-1][:progress], "\n"
      # end
    end

    it "should be greather than 0.97 for singlenode deployment" do
      nodes = [
        {'uid' => '1', 'ip' => '1.0.0.1', 'fqdn' => 'slave-1.domain.tld', 'role' => 'controller', 'src_filename' => 'puppet-agent.log.singlenode'},
      ]

      calculated_nodes = deployment_parser_wrapper('singlenode', nodes)
      calculated_nodes.each {|node| node['statistics']['pcc'].should > 0.97}
    end

    it "should be greather than 0.94 for multinode deployment" do
      nodes = [
        {'uid' => '1', 'ip' => '1.0.0.1', 'fqdn' => 'slave-1.domain.tld', 'role' => 'controller', 'src_filename' => 'puppet-agent.log.multi.contr'},
        {'uid' => '2', 'ip' => '1.0.0.2', 'fqdn' => 'slave-2.domain.tld', 'role' => 'compute', 'src_filename' => 'puppet-agent.log.multi.compute'},
      ]

      calculated_nodes = deployment_parser_wrapper('multinode', nodes)
      calculated_nodes.each {|node| node['statistics']['pcc'].should > 0.94}
    end

  end
end
