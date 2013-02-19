require 'date'

module Astute
  module LogParser
    class ParseProvisionLogs <ParseNodeLogs
      def initialize
        pattern_spec = Patterns::get_default_pattern('anaconda-log-supposed-time-kvm')
        super(pattern_spec)
      end

      def progress_calculate(uids_to_calc, nodes)
        # Just create correct pattern for each node and then call parent method.
        uids_to_calc.each do |uid|
          node = nodes.select {|n| n['uid'] == uid}[0]
          unless @nodes_states[uid]
            @nodes_states[uid] = get_pattern_for_node(node)
          end
        end
        super(uids_to_calc, nodes)
      end

      private
      def calculate(fo, node_pattern_spec)
        case node_pattern_spec['type']
        when 'pattern-list'
          progress = simple_pattern_finder(fo, node_pattern_spec)
        when 'supposed-time'
          progress = supposed_time_parser(fo, node_pattern_spec)
        end
        return progress
      end

      def get_pattern_for_node(node)
        if node['manufacturer'] == 'KVM'
          pattern_spec = Patterns::get_default_pattern('anaconda-log-supposed-time-kvm')
        else
          pattern_spec = Patterns::get_default_pattern('anaconda-log-supposed-time-baremetal')
        end
        pattern_spec['path_prefix'] ||= PATH_PREFIX.to_s
        pattern_spec['separator'] ||= SEPARATOR.to_s

        hdd = node['meta']['disks'].select{|disk| not disk['removable']}[0]
        if hdd
          # Convert size from bytes to GB
          hdd_size = hdd['size'] / 10 ** 9
        else
          # Default hdd size is 20 GB
          hdd_size = 20
        end

        hdd_pattern = pattern_spec['pattern_list'].select {|el| el['hdd_size_multiplier']}[0]
        hdd_pattern['supposed_time'] = (hdd_pattern['hdd_size_multiplier'] * hdd_size).to_i
        return pattern_spec
      end

	    def supposed_time_parser(fo, pattern_spec)
	      # Pattern specification example:
	      # pattern_spec = {'type' => 'supposed-time',
	      #   'chunk_size' => 10000,
	      #   'date_format' => '%Y-%m-%dT%H:%M:%S',
	      #   'date_regexp' => '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
	      #   'pattern_list' => [
	      #     {'pattern' => 'Running anaconda script', 'supposed_time' => 60},
	      #     {'pattern' => 'moving (1) to step enablefilesystems', 'supposed_time' => 3},
	      #     {'pattern' => "notifying kernel of 'change' event on device", 'supposed_time' => 200},
	      #     {'pattern' => 'Preparing to install packages', 'supposed_time' => 9},
	      #     {'pattern' => 'Installing glibc-common-2.12', 'supposed_time' => 9},
	      #     {'pattern' => 'Installing bash-4.1.2', 'supposed_time' => 11},
	      #     {'pattern' => 'Installing coreutils-8.4-19', 'supposed_time' => 20},
	      #     {'pattern' => 'Installing centos-release-6-3', 'supposed_time' => 21},
	      #     {'pattern' => 'Installing attr-2.4.44', 'supposed_time' => 23},
	      #     {'pattern' => 'leaving (1) step installpackages', 'supposed_time' => 60},
	      #     {'pattern' => 'moving (1) to step postscripts', 'supposed_time' => 4},
	      #     {'pattern' => 'leaving (1) step postscripts', 'supposed_time' => 130},
	      #     ].reverse,
	      #   'filename' => 'install/anaconda.log'
	      #   }
	      # Use custom separator if defined.
	      separator = pattern_spec['separator']
	      log_patterns = pattern_spec['pattern_list']
	      date_format = pattern_spec['date_format']
	      date_regexp = pattern_spec['date_regexp']
	      unless date_regexp and date_format and log_patterns
	        Astute.logger.warn("Wrong pattern_spec #{pattern_spec.inspect} defined for calculating progress via logs.")
	        return 0
	      end

	      def self.get_elapsed_time(patterns)
	        elapsed_time = 0
	        patterns.each do |p|
	          if p['_progress']
	            break
	          else
	            elapsed_time += p['supposed_time']
	          end
	        end
	        return elapsed_time
	      end

	      def self.get_progress(base_progress, elapsed_time, delta_time, supposed_time=nil)
	        return 1.0 if elapsed_time.zero?
	        k = (1.0 - base_progress) / elapsed_time
	        supposed_time ? surplus = delta_time - supposed_time : surplus = nil
	        if surplus and surplus > 0
	          progress = supposed_time * k + surplus * k/3 + base_progress
	        else
	          progress = delta_time * k + base_progress
	        end
	        progress = 1.0 if progress > 1
	        return progress
	      end

	      def self.get_seconds_from_time(date)
	        hours, mins, secs, frac = Date::day_fraction_to_time(date)
	        return hours*60*60 + mins*60 + secs
	      end


	      chunk = get_chunk(fo, pattern_spec['chunk_size'])
	      return 0 unless chunk
	      pos = chunk.rindex(separator)
	      chunk = chunk.slice((pos + separator.size)..-1) if pos
	      block = chunk.split("\n")

	      now = DateTime.now()
	      prev_time = pattern_spec['_prev_time'] ||= now
	      prev_progress = pattern_spec['_prev_progress'] ||= 0
	      elapsed_time = pattern_spec['_elapsed_time'] ||= get_elapsed_time(log_patterns)
	      seconds_since_prev = get_seconds_from_time(now - prev_time)

	      until block.empty?
	        string = block.pop
	        log_patterns.each do |pattern|
	          if string.include?(pattern['pattern'])
	            if pattern['_progress']
	              # We not found any new messages. Calculate progress with old data.
	              progress = get_progress(prev_progress, elapsed_time,
	                                      seconds_since_prev, pattern['supposed_time'])
	              return progress

	            else
	              # We found message that we never find before. We need to: 
	              # calculate progress for this message;
	              # recalculate control point and elapsed_time;
	              # calculate progress for current time.

	              # Trying to find timestamp of message.
	              date_string = string.match(date_regexp)
	              if date_string
	                # Get relative time when the message realy occured.
	                date = DateTime.strptime(date_string[0], date_format) - prev_time.offset
	                real_time = get_seconds_from_time(date - prev_time)
	                # Update progress of the message.
	                prev_supposed_time = log_patterns.select{|n| n['_progress'] == prev_progress}[0]
	                prev_supposed_time = prev_supposed_time['supposed_time'] if prev_supposed_time
	                progress = get_progress(prev_progress, elapsed_time, real_time, prev_supposed_time)
	                pattern['_progress'] = progress
	                # Recalculate elapsed time.
	                elapsed_time = pattern_spec['_elapsed_time'] = get_elapsed_time(log_patterns)
	                # Update time and progress for control point.
	                prev_time = pattern_spec['_prev_time'] = date
	                prev_progress = pattern_spec['_prev_progress'] = progress
	                seconds_since_prev = get_seconds_from_time(now - date)
	                # Calculate progress for current time.
	                progress = get_progress(prev_progress, elapsed_time,
	                                        seconds_since_prev, pattern['supposed_time'])
	                return progress
	              else
	                Astute.logger.info("Can't gather date (format: '#{date_regexp}') from string: #{string}")
	              end
	            end
	          end
	        end
	      end
	      # We found nothing.
	      progress = get_progress(prev_progress, elapsed_time, seconds_since_prev, log_patterns[0]['supposed_time'])
	      return progress
	    end

	    def simple_pattern_finder(fo, pattern_spec)
	      # Pattern specification example:
	      # pattern_spec = {'type' => 'pattern-list', 'separator' => "custom separator\n",
	      #   'chunk_size' => 40000,
	        # 'pattern_list' => [
	        #   {'pattern' => 'Running kickstart %%pre script', 'progress' => 0.08},
	        #   {'pattern' => 'to step enablefilesystems', 'progress' => 0.09},
	        #   {'pattern' => 'to step reposetup', 'progress' => 0.13},
	        #   {'pattern' => 'to step installpackages', 'progress' => 0.16},
	        #   {'pattern' => 'Installing',
	        #     'number' => 210, # Now it install 205 packets. Add 5 packets for growth in future.
	        #     'p_min' => 0.16, # min percent
	        #     'p_max' => 0.87 # max percent
	        #     },
	        #   {'pattern' => 'to step postinstallconfig', 'progress' => 0.87},
	        #   {'pattern' => 'to step dopostaction', 'progress' => 0.92},
	        #   ]
	        # }
	      # Use custom separator if defined.
	      separator = pattern_spec['separator']
	      log_patterns = pattern_spec['pattern_list']
	      unless log_patterns
	        Astute.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via logs.")
	        return 0
	      end

	      chunk = get_chunk(fo, pattern_spec['chunk_size'])
	      # NOTE(mihgen): Following line fixes "undefined method `rindex' for nil:NilClass" for empty log file
	      return 0 unless chunk
	      pos = chunk.rindex(separator)
	      chunk = chunk.slice((pos + separator.size)..-1) if pos
	      block = chunk.split("\n")
	      return 0 unless block
	      while true
	        string = block.pop
	        return 0 unless string # If we found nothing
	        log_patterns.each do |pattern|
	          if string.include?(pattern['pattern'])
	            return pattern['progress'] if pattern['progress']
	            if pattern['number']
	              string = block.pop
	              counter = 1
	              while string
	                counter += 1 if string.include?(pattern['pattern'])
	                string = block.pop
	              end
	              progress = counter.to_f / pattern['number']
	              progress = 1 if progress > 1
	              progress = pattern['p_min'] + progress * (pattern['p_max'] - pattern['p_min'])
	              return progress
	            end
	            Astute.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via log.")
	          end
	        end
	      end
	    end

    end
  end
end