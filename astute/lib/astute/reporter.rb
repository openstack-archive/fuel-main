require 'set'

STATES = {'offline' => 0,
          'discover' => 10,
          'verification' => 20,
          'provisioning' => 30,
          'provisioned' => 40,
          'deploying' => 50,
          'ready' => 60,
          'error' => 70}

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
        node = validate(node)
        node_here = @nodes.select {|x| x['uid'] == node['uid']}
        if node_here.empty?
          nodes_to_report << node
          next
        end
        node_here = node_here[0]

        # We need to update node here only if progress is greater, or status changed
        if node_here.eql?(node)
          next
        end

        unless node['status'].nil?
          node_here_state = (STATES[node_here['status']] or 0)
          if STATES[node['status']] < node_here_state
            Astute.logger.error("Attempt to assign lower status detected: "\
                                "Status was: #{node_here['status']}, attempted to "\
                                "assign: #{node['status']}. Skipping this node (id=#{node['uid']})")
            next
          end
        end

        nodes_to_report << node
      end
      # Let's report only if nodes updated
      if nodes_to_report.any?
        data['nodes'] = nodes_to_report
        @up_reporter.report(data)
        # Replacing current list of nodes with the updated one, keeping not updated elements
        uids = nodes_to_report.map {|x| x['uid']}
        @nodes.delete_if {|x| uids.include?(x['uid'])}
        @nodes.concat(nodes_to_report)
      end
    end

    private
    def validate(node)
      err = ''
      unless node['status'].nil?
        err += "Status provided #{node['status']} is not supported." if STATES[node['status']].nil?
      end
      unless node['uid']
        err += "node uid is not provided."
      end
      unless node['progress'].nil?
        err = "progress value provided, but no status." if node['status'].nil?
      end
      raise "Validation of node: #{node.inspect} for report failed: #{err}" if err.any?

      unless node['progress'].nil?
        if node['progress'] > 100
          Astute.logger.error("Passed report for node with progress > 100: "\
                              "#{node.inspect}. Adjusting progress to 100.")
          node['progress'] = 100
        end
        unless node['status'].nil?
          if node['status'] == 'ready' and node['progress'] != 100
            Astute.logger.error("In ready state node should have progress 100, "\
                                "but node passed: #{node.inspect}. Setting it to 100")
            node['progress'] = 100
          end
          if node['status'] == 'verification'
            # FIXME(mihgen): Currently our backend doesn't support such status. So let's just remove it...
            node.delete('status')
          end
        end
      end
      return node
    end
  end
end
