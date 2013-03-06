require 'set'

STATES = {
  'offline'      => 0,
  'discover'     => 10,
  'provisioning' => 30,
  'provisioned'  => 40,
  'deploying'    => 50,
  'ready'        => 60,
  'error'        => 70
}

module Astute
  class ProxyReporter
    def initialize(up_reporter)
      @up_reporter = up_reporter
      @nodes = []
    end

    def report(data)
      nodes_to_report = []
      nodes = (data['nodes'] or [])
      nodes.each do |node|
        node = node_validate(node)
        nodes_to_report << node if node
      end
      # Let's report only if nodes updated
      if nodes_to_report.any?
        data['nodes'] = nodes_to_report
        @up_reporter.report(data)
        # Update nodes attributes in @nodes.
        nodes_to_report.each do |node|
          saved_node = @nodes.select {|x| x['uid'] == node['uid']}.first  # NOTE: use nodes hash
          if saved_node
            node.each {|k, v| saved_node[k] = v}
          else
            @nodes << node
          end
        end
      end
    end

  private

    def node_validate(node)
      # Validate basic correctness of attributes.
      err = []
      if node['status'].nil?
        err << "progress value provided, but no status" unless node['progress'].nil?
      else
        err << "Status provided #{node['status']} is not supported" if STATES[node['status']].nil?
      end
      unless node['uid']
        err << "Node uid is not provided"
      end
      if err.any?
        msg = "Validation of node: #{node.inspect} for report failed: #{err.join('; ')}."
        Astute.logger.error(msg)
        raise msg
      end

      # Validate progress field.
      unless node['progress'].nil?
        if node['progress'] > 100
          Astute.logger.warn("Passed report for node with progress > 100: "\
                              "#{node.inspect}. Adjusting progress to 100.")
          node['progress'] = 100
        end
        if node['progress'] < 0
          Astute.logger.warn("Passed report for node with progress < 0: "\
                              "#{node.inspect}. Adjusting progress to 0.")
          node['progress'] = 0
        end
      end
      if not node['status'].nil? and ['provisioned', 'ready'].include?(node['status']) and node['progress'] != 100
        Astute.logger.warn("In #{node['status']} state node should have progress 100, "\
                            "but node passed: #{node.inspect}. Setting it to 100")
        node['progress'] = 100
      end

      # Comparison with previous state.
      saved_node = @nodes.select {|x| x['uid'] == node['uid']}.first
      unless saved_node.nil?
        saved_status = (STATES[saved_node['status']] or 0)
        node_status = (STATES[node['status']] or saved_status)
        saved_progress = (saved_node['progress'] or 0)
        node_progress = (node['progress'] or saved_progress)

        if node_status < saved_status
          Astute.logger.warn("Attempt to assign lower status detected: "\
                             "Status was: #{saved_status}, attempted to "\
                             "assign: #{node_status}. Skipping this node (id=#{node['uid']})")
          return
        end
        if node_progress < saved_progress and node_status == saved_status
          Astute.logger.warn("Attempt to assign lesser progress detected: "\
                             "Progress was: #{saved_progress}, attempted to "\
                             "assign: #{node_progress}. Skipping this node (id=#{node['uid']})")
          return
        end

        # We need to update node here only if progress is greater, or status changed
        return if node.select{|k, v| not saved_node[k].eql?(v)}.empty?
      end

      node
    end
  end
end
