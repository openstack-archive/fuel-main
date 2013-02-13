require 'date'

module Astute
  module LogParser
    # Default values. Can be overrided by pattern_spec.
    # E.g. pattern_spec = {'separator' => 'new_separator', ...}
    @separator = "SEPARATOR\n"
    @log_portion = 10000

    class NoParsing
      def initialize(*args)
      end

      def method_missing(*args)
        # We just eat the call if we don't want to deal with logs
      end

      def progress_calculate(*args)
        []
      end
    end

    class ParseNodeLogs
      require 'astute/logparser_patterns'
      attr_reader :pattern_spec
      @@path_prefix = '/var/log/remote/'

      def initialize(pattern_spec)
        @nodes_states = {}
        pattern_spec['path_prefix'] ||= @@path_prefix.dup
        @pattern_spec = pattern_spec
      end

      def progress_calculate(uids_to_calc, nodes)
        nodes_progress = []
        uids_to_calc.each do |uid|
          node = nodes.select {|n| n['uid'] == uid}[0]
          path = "#{@pattern_spec['path_prefix']}#{node['ip']}/#{@pattern_spec['filename']}"
          node_pattern_spec = @nodes_states[uid]
          unless node_pattern_spec
            node_pattern_spec = Marshal.load(Marshal.dump(@pattern_spec))
            @nodes_states[uid] = node_pattern_spec
          end

          nodes_progress << {
            'uid' => uid,
            'progress' => (LogParser::get_log_progress(path, node_pattern_spec)*100).to_i # Return percent of progress
          }
        end
        return nodes_progress
      end

      def pattern_spec= (pattern_spec)
        @nodes_states = {}
        pattern_spec['path_prefix'] ||= @@path_prefix.dup
        @pattern_spec = pattern_spec
      end

      def add_separator(nodes)
        nodes.each do |node|
          path = "#{@pattern_spec['path_prefix']}#{node['ip']}/#{@pattern_spec['filename']}"
          LogParser::add_log_separator(path)
        end
      end
    end

    class ParseDeployLogs <ParseNodeLogs
      attr_reader :deploy_type
      def initialize(deploy_type='multinode_compute')
        @deploy_type = deploy_type
        pattern_spec = LogParser::get_default_pattern(
          "puppet-log-components-list-#{@deploy_type}-controller")
        super(pattern_spec)
      end

      def deploy_type= (deploy_type)
        @deploy_type = deploy_type
        @nodes_states = {}
      end

      def progress_calculate(uids_to_calc, nodes)
        # Just create correct pattern for each node and then call parent method.
        uids_to_calc.each do |uid|
          node = nodes.select {|n| n['uid'] == uid}[0]
          unless @nodes_states[uid]
            @nodes_states[uid] = LogParser::get_default_pattern(
              "puppet-log-components-list-#{@deploy_type}-#{node['role']}")
          end
        end
        super(uids_to_calc, nodes)
      end

    end

    class ParseProvisionLogs <ParseNodeLogs
      def initialize
        pattern_spec = LogParser.get_default_pattern('anaconda-log-supposed-time')
        super(pattern_spec)
      end
    end


    public
    def self.add_log_separator(path, separator=@separator)
      File.open(path, 'a') {|fo| fo.write separator } if File.readable?(path)
    end

    def self.get_log_progress(path, node_pattern_spec)
      unless File.readable?(path)
        Astute.logger.debug "Can't read file with logs: #{path}"
        return 0
      end
      if node_pattern_spec.nil?
        Astute.logger.warn "Can't parse logs. Pattern_spec is empty."
        return 0
      end
      progress = nil
      File.open(path) do |fo|
        # Try to find well-known ends of log.
        endlog = find_endlog_patterns(fo, node_pattern_spec)
        return endlog if endlog
        # Start reading from end of file.
        fo.pos = fo.stat.size

        case node_pattern_spec['type']
        when 'count-lines'
          progress = simple_line_counter(fo, node_pattern_spec)
        when 'pattern-list'
          progress = simple_pattern_finder(fo, node_pattern_spec)
        when 'supposed-time'
          progress = supposed_time_parser(fo, node_pattern_spec)
        when 'components-list'
          progress = component_parser(fo, node_pattern_spec)
        end
      node_pattern_spec['file_pos'] = fo.pos
      end
      unless progress
        Astute.logger.warn("Wrong pattern #{node_pattern_spec.inspect} defined for calculating progress via logs.")
        return 0
      end
      return progress
    end

    private

    def self.supposed_time_parser(fo, pattern_spec)
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
      separator = @separator unless separator
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
      progress = get_progress(prev_progress, elapsed_time, seconds_since_start, log_patterns[0]['supposed_time'])
      return progress
    end

    def self.simple_pattern_finder(fo, pattern_spec)
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
      separator = @separator unless separator
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

    def self.find_endlog_patterns(fo, pattern_spec)
      # Pattern example:
      # pattern_spec = {...,
      #   'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
      # }      
      endlog_patterns = pattern_spec['endlog_patterns']
      return nil unless endlog_patterns
      fo.pos = fo.stat.size
      chunk = get_chunk(fo, 100)
      return nil unless chunk
      endlog_patterns.each do |pattern|
        return pattern['progress'] if chunk.end_with?(pattern['pattern'])
      end
      return nil
    end

    def self.simple_line_counter(fo, pattern_spec)
      # Pattern specification example:
      # pattern_spec = {'type' => 'count-lines',
      #   'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
      #   'expected_line_number' => 500}
      # Use custom separator if defined.
      separator = pattern_spec['separator']
      separator = @separator unless separator
      counter = 0
      end_of_scope = false
      previous_subchunk = ''
      until end_of_scope
        chunk = get_chunk(fo, pattern_spec['chunk_size'])
        break unless chunk
        # Trying to find separator on border between chunks.
        subchunk = chunk.slice((1-separator.size)..-1)
        # End of file reached. Exit from cycle.
        end_of_scope = true unless subchunk
        if subchunk and (subchunk + previous_subchunk).include?(separator)
          # Separator found on border between chunks. Exit from cycle.
          end_of_scope = true
          continue
        end

        pos = chunk.rindex(separator)
        if pos
          end_of_scope = true
          chunk = chunk.slice((pos + separator.size)..-1)
        end
        counter += chunk.count("\n")
      end
      number = pattern_spec['expected_line_number']
      unless number
        Astute.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via log.")
        return 0
      end
      progress = counter.to_f / number
      progress = 1 if progress > 1
      return progress
    end

    def self.get_chunk(fo, size=nil, pos=nil)
      if pos
        fo.pos = pos
        return fo.read
      end
      size = @log_portion unless size
      return nil if fo.pos == 0
      size = fo.pos if fo.pos < size
      next_pos = fo.pos - size
      fo.pos = next_pos
      block = fo.read(size)
      fo.pos = next_pos
      return block
    end

    def self.component_parser(fo, pattern_spec)
      # Pattern specification example:
      # pattern_spec = {'type' => 'components-list',
      #   'chunk_size' => 40000,
        # 'components_list' => [
        #   {'name' => 'Horizon', 'weight' => 10, 'patterns' => [
        #      {'pattern' => '/Stage[main]/Horizon/Package[mod_wsgi]/ensure) created', 'progress' => 0.1},
        #      {'pattern' => '/Stage[main]/Horizon/File_line[horizon_redirect_rule]/ensure) created', 'progress' => 0.3},
        #      {'pattern' => '/Stage[main]/Horizon/File[/etc/openstack-dashboard/local_settings]/group)', 'progress' => 0.7},
        #      {'pattern' => '/Stage[main]/Horizon/Service[$::horizon::params::http_service]/ensure)'\
        #                    ' ensure changed \'stopped\' to \'running\'', 'progress' => 1},
        #      ]
        #   },
        #   ]
        # }
      # Use custom separator if defined.
      separator = pattern_spec['separator']
      separator = @separator unless separator
      components_list = pattern_spec['components_list']
      unless components_list
        Astute.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via logs.")
        return 0
      end

      chunk = get_chunk(fo, pos=pattern_spec['file_pos'])
      return 0 unless chunk
      pos = chunk.rindex(separator)
      chunk = chunk.slice((pos + separator.size)..-1) if pos
      block = chunk.split("\n")

      # Update progress of each component.
      while block.any?
        string = block.pop
        components_list.each do |component|
          matched_pattern = nil
          component['patterns'].each do |pattern|
            if pattern['regexp']
              matched_pattern = pattern if string.match(pattern['pattern'])
            else
              matched_pattern = pattern if string.include?(pattern['pattern'])
            end
            break if matched_pattern
          end
          if matched_pattern and
              (not component['_progress'] or matched_pattern['progress'] > component['_progress'])
            component['_progress'] = matched_pattern['progress']
          end
        end
      end

      # Calculate integral progress.
      weighted_components = components_list.select{|n| n['weight']}
      weight_sum = 0.0
      if weighted_components.any?
        weighted_components.each{|n| weight_sum += n['weight']}
        weight_sum = weight_sum * components_list.length / weighted_components.length
        raise "Total weight of weighted components equal to zero." if weight_sum == 0
      end
      nonweighted_delta = 1.0 / components_list.length
      progress = 0
      components_list.each do |component|
        component['_progress'] = 0.0 unless component['_progress']
        weight = component['weight']
        if weight
          progress += component['_progress'] * weight / weight_sum
        else
          progress += component['_progress'] * nonweighted_delta
        end
      end

      return progress
    end
  end
end
