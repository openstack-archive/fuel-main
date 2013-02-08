#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")
require 'tempfile'
require 'date'

include Astute

describe LogParser do
  context "Pattern-based progress bar calculation (anaconda.log)" do
    before :each do
      @pattern_spec = {'type' => 'pattern-list', 'chunk_size' =>  40000, # Size of block which reads for pattern searching.
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
          {'pattern' => 'to step postinstallconfig', 'progress' => 0.87},
          {'pattern' => 'to step dopostaction', 'progress' => 0.92},
        ].reverse
      }
    end

    def test_supposed_time_parser(pattern_spec)
      date_regexp = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
      date_format = '%Y-%m-%dT%H:%M:%S'
      fo = Tempfile.new('logparse')
      logfile = File.join(File.dirname(__FILE__), "..", "example-logs", "anaconda.log_")
      path = fo.path
      initial_progress = Astute::LogParser.get_log_progress(path, pattern_spec)
      initial_progress.should eql(0)

      progress_table = []
      File.open(logfile).each do |line|
        fo.write(line)
        fo.flush
        date_string = line.match(date_regexp)
        if date_string
          date = DateTime.strptime(date_string[0], date_format)
          progress = Astute::LogParser.get_log_progress(path, pattern_spec)
          progress_table << {'date' => date, 'progress' => progress}
        end
      end
      fo.close!
      first_event_date, first_progress = progress_table[0]['date'], progress_table[0]['progress']
      last_event_date, last_progress = progress_table[-1]['date'], progress_table[-1]['progress']
      period = (last_event_date - first_event_date) / (last_progress - first_progress)
      hours, mins, secs, frac = Date::day_fraction_to_time(period)
      # FIXME(mihgen): I hope this calculation can be much simplified: needs refactoring
      # Assuming server was in reboot for reboot_time
      reboot_time = 30
      # period will be useful for other test cases
      period_in_sec = hours * 60 * 60 + mins * 60 + secs + reboot_time

      # Let's normalize the time in table
      progress_table.each do |el|
        delta = el['date'] - first_event_date
        hours, mins, secs, frac = Date::day_fraction_to_time(delta)
        delta_in_sec = hours * 60 * 60 + mins * 60 + secs
        el['time'] = delta_in_sec + reboot_time
      end
      return progress_table, period_in_sec
    end

    def test_independed_parser(pattern_spec, logfile,
        date_regexp='^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        date_format='%Y-%m-%dT%H:%M:%S')
      # Copy logs line by line from example logfile to tempfile and collect progress for each step.
      # Also calculate some statistics variables: expectancy, standart deviation and
      # correlation coefficient between real and ideal progress calculation.
      fo = Tempfile.new('logparse')
      path = fo.path
      initial_progress = Astute::LogParser.get_log_progress(path, pattern_spec)
      initial_progress.should eql(0)

      progress_table = []
      reboot_time = 30
      first_event_date = nil
      total_time = 0
      real_expectancy = 0
      real_sqr_expectancy = 0
      File.open(logfile).each do |line|
        fo.write(line)
        fo.flush
        date_string = line.match(date_regexp)
        if date_string
          date = DateTime.strptime(date_string[0], date_format)
          prev_event_date = date unless prev_event_date
          progress = Astute::LogParser.get_log_progress(path, pattern_spec)
          period = date - prev_event_date
          hours, mins, secs, frac = Date::day_fraction_to_time(period)
          period_in_sec = hours * 60 * 60 + mins * 60 + secs + reboot_time
          total_time += period_in_sec
          real_expectancy += period_in_sec * progress
          real_sqr_expectancy += period_in_sec * progress ** 2
          progress_table << {'time_delta' => period_in_sec, 'progress' => progress}
        end
      end
      fo.close!

      # Calculate standart deviation for real progress distibution.
      real_expectancy = real_expectancy.to_f / total_time
      real_sqr_expectancy = real_sqr_expectancy.to_f / total_time
      real_standart_deviation = (real_sqr_expectancy - real_expectancy ** 2) ** 0.5

      # Calculate PCC (correlation coefficient).
      ideal_sqr_expectancy = 0
      t = 0
      ideal_delta = 1.0 / total_time
      mixed_expectancy = 0
      progress_table.each do |el|
        t += el['time_delta']
        ideal_progress = t * ideal_delta
        ideal_sqr_expectancy += ideal_progress ** 2 * el['time_delta']
        el['ideal_progress'] = ideal_progress
        mixed_expectancy += el['progress'] * ideal_progress * el['time_delta']
      end

      ideal_expectancy = 0.5
      ideal_sqr_expectancy = ideal_sqr_expectancy / total_time
      mixed_expectancy = mixed_expectancy / total_time
      ideal_standart_deviation = (ideal_sqr_expectancy - ideal_expectancy ** 2) ** 0.5
      covariance = mixed_expectancy - ideal_expectancy * real_expectancy
      pcc = covariance / (ideal_standart_deviation * real_standart_deviation)

      statistics = {
        'real_expectancy' => real_expectancy,
        'real_sqr_expectancy' => real_sqr_expectancy,
        'real_standart_deviation' => real_standart_deviation,
        'ideal_sqr_expectancy' => ideal_sqr_expectancy,
        'ideal_standart_deviation' => ideal_standart_deviation,
        'mixed_expectancy' => mixed_expectancy,
        'covariance' => covariance,
        'pcc' => pcc,
        'total_time' => total_time,
        'progress_table' => progress_table
      }

      return statistics
    end

    it "new progress must be equal or greater than previous" do
      progress_table, period_in_sec = test_supposed_time_parser(@pattern_spec)
      progress_table.each_cons(2) do |el|
        el[1]['progress'].should be >= el[0]['progress']
        el[0]['progress'].should be >= 0
        el[1]['progress'].should be <= 1
      end
    end

    it "test component based progress calculation with different logfiles" do
      default_patterns = Astute::LogParser.list_default_patterns
      default_patterns.each do |pattern_name|
        pattern_spec = Astute::LogParser.get_default_pattern(pattern_name)
        filenames = Dir.glob(File.join(File.dirname(__FILE__), "..", "example-logs", "puppet-agent*"))
        filenames.each do |logfile|
          statistics = test_independed_parser(pattern_spec, logfile)
          statistics.delete('progress_table')
          p "\n#{logfile}"
          p statistics
        end
      end
    end




    it "it should move smoothly"
    it "it must be updated at least 5 times" do
      # Otherwise progress bar has no meaning I guess...
      pending('Not yet implemented')
    end

  end
end

    #pattern_spec = {'type' => 'supposed_time',
      #'chunk_size' => 10000,
      #'date_format' => '%Y-%m-%dT%H:%M:%S',
      #'date_regexp' => '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
      #'pattern_list' => [
        #{'pattern' => 'Running anaconda script', 'supposed_time' => 60},
        #{'pattern' => 'moving (1) to step enablefilesystems', 'supposed_time' => 3},
        #{'pattern' => "notifying kernel of 'change' event on device", 'supposed_time' => 97},
        #{'pattern' => 'Preparing to install packages', 'supposed_time' => 8},
        #{'pattern' => 'Installing glibc-common-2.12', 'supposed_time' => 9},
        #{'pattern' => 'Installing bash-4.1.2', 'supposed_time' => 10},
        #{'pattern' => 'Installing coreutils-8.4-19', 'supposed_time' => 20},
        #{'pattern' => 'Installing centos-release-6-3', 'supposed_time' => 20},
        #{'pattern' => 'Installing attr-2.4.44', 'supposed_time' => 19},
        #{'pattern' => 'leaving (1) step installpackages', 'supposed_time' => 51},
        #{'pattern' => 'moving (1) to step postscripts', 'supposed_time' => 3},
        #{'pattern' => 'leaving (1) step postscripts', 'supposed_time' => 132},
        #].reverse,
      #}
