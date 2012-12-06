module Astute
  module LogParser
    @separator = "SEPARATOR\n"
    @log_portion = 10000

    class ParseNodeLogs
      attr_accessor :pattern_spec

      def initialize(filename, pattern_spec)
        @filename = filename
        @pattern_spec = pattern_spec
      end

      def progress_calculate(nodes)
        return 0 if nodes.empty?
        nodes_progress = []
        nodes.each do |node|
          path = "/var/log/remote/#{node['ip']}/#{@filename}"
          nodes_progress << {
            'uid' => node['uid'],
            'progress' => (LogParser::get_log_progress(path, @pattern_spec)*100).to_i # Return percent of progress
          }
        end
        return nodes_progress
      end

      def add_separator(nodes)
        nodes.each do |node|
          path = "/var/log/remote/#{node['ip']}/#{@filename}"
          LogParser::add_log_separator(path)
        end
      end
    end


    public
    def self.add_log_separator(path, separator=@separator)
      File.open(path, 'a') {|fo| fo.write separator } if File.readable?(path)
    end

    def self.get_log_progress(path, pattern_spec)
      # Pattern specification example:
      # pattern_spec = {'type' => 'pattern-list', 'separator' => "custom separator\n",
      #   'chunk_size' => 10000,
      #   'pattern_list' => [
      #     {'pattern' => 'to step installpackages', 'progress' => 0.16},
      #     {'pattern' => 'Installing',
      #       'number' => 210, # Now it install 205 packets. Add 5 packets for growth in future.
      #       'p_min' => 0.16, # min percent
      #       'p_max' => 0.87 # max percent
      #       }
      #     ]
      #   }

      return 0 unless File.readable?(path)
      progress = nil
      File.open(path) do |fo|
        # Try to find well-known ends of log.
        endlog = find_endlog_patterns(fo, pattern_spec)
        return endlog if endlog
        # Start reading from end of file.
        fo.pos = fo.stat.size

        if pattern_spec['type'] == 'count-lines'
          progress = simple_line_counter(fo, pattern_spec)
        elsif pattern_spec['type'] = 'pattern-list'
          progress = simple_pattern_finder(fo, pattern_spec)
        end
      end
      unless progress
        Naily.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via logs.")
        return 0
      end
      return progress
    end

    private
    def self.simple_pattern_finder(fo, pattern_spec)
      # Use custom separator if defined.
      separator = pattern_spec['separator']
      separator = @separator unless separator
      log_patterns = pattern_spec['pattern_list']
      unless log_patterns
        Naily.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via logs.")
        return 0
      end

      chunk = get_chunk(fo, pattern_spec['chunk_size'])
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
            Naily.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via log.")
          end
        end
      end
    end

    def self.find_endlog_patterns(fo, pattern_spec)
      endlog_patterns = pattern_spec['endlog_patterns']
      return nil unless endlog_patterns
      fo.pos = fo.stat.size
      chunk = get_chunk(fo, 100)
      endlog_patterns.each do |pattern|
        return pattern['progress'] if chunk.end_with?(pattern['pattern'])
      end
      return nil
    end

    def self.simple_line_counter(fo, pattern_spec)
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
        Naily.logger.warn("Wrong pattern #{pattern_spec.inspect} defined for calculating progress via log.")
        return 0
      end
      progress = counter.to_f / number
      progress = 1 if progress > 1
      return progress
    end

    def self.get_chunk(fo, size=nil)
      size = @log_portion unless size
      return nil if fo.pos == 0
      size = fo.pos if fo.pos < size
      next_pos = fo.pos - size
      fo.pos = next_pos
      block = fo.read(size)
      fo.pos = next_pos
      return block
    end
  end
end
