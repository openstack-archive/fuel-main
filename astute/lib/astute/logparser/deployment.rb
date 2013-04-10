module Astute
  module LogParser
    class ParseDeployLogs <ParseNodeLogs
      attr_reader :deploy_type
      def initialize(deploy_type='multinode')
        @deploy_type = deploy_type
        pattern_spec = Patterns::get_default_pattern(
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
            pattern_spec = Patterns::get_default_pattern(
              "puppet-log-components-list-#{@deploy_type}-#{node['role']}")
            pattern_spec['path_prefix'] ||= PATH_PREFIX.to_s
            pattern_spec['separator'] ||= SEPARATOR.to_s
            @nodes_states[uid] = pattern_spec
          end
        end
        super(uids_to_calc, nodes)
      end

      private
      def calculate(fo, node_pattern_spec)
        case node_pattern_spec['type']
        when 'count-lines'
          progress = simple_line_counter(fo, node_pattern_spec)
        when 'components-list'
          progress = component_parser(fo, node_pattern_spec)
        end
        return progress
      end

	    def simple_line_counter(fo, pattern_spec)
	      # Pattern specification example:
	      # pattern_spec = {'type' => 'count-lines',
	      #   'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
	      #   'expected_line_number' => 500}
	      # Use custom separator if defined.
	      separator = pattern_spec['separator']
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

	    def component_parser(fo, pattern_spec)
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
end
