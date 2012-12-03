require 'json'
require 'ipaddr'

module Astute
  module Metadata
    def self.publish_facts(ctx, uid, metadata)
      # This is synchronious RPC call, so we are sure that data were sent and processed remotely
      Astute.logger.debug "#{ctx.task_id}: nailyfact - storing metadata for node uid=#{uid}"
      nailyfact = MClient.new(ctx, "nailyfact", uid)
      # TODO(mihgen) check results!
      stats = nailyfact.post(:value => metadata.to_json)
    end
  end
end
