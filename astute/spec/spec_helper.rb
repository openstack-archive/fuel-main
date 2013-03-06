$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'rspec'
# Following require is needed for rcov to provide valid results
require 'rspec/autorun'
require 'yaml'
require 'astute'

RSpec.configure do |config|
  config.mock_with :mocha
end

# NOTE(mihgen): I hate to wait for unit tests to complete,
#               resetting time to sleep significantly increases tests speed
Astute.config.PUPPET_DEPLOY_INTERVAL = 0
Astute.config.PUPPET_FADE_INTERVAL = 0
Astute.config.MC_RETRY_INTERVAL = 0

module SpecHelpers
  def mock_rpcclient(discover_nodes=nil, timeout=nil)
    rpcclient = mock('rpcclient') do
      stubs(:progress=)
      unless timeout.nil?
        expects(:timeout=).with(timeout)
      end
      unless discover_nodes.nil?
        expects(:discover).with(:nodes => discover_nodes.map{|x| x['uid'].to_s}).at_least_once
      else
        stubs(:discover)
      end
    end
    Astute::MClient.any_instance.stubs(:rpcclient).returns(rpcclient)
    return rpcclient
  end

  def mock_mc_result(result={})
    mc_res = {:statuscode => 0, :data => {}, :sender => '1'}
    mc_res.merge!(result)
    mc_result = mock('mc_result') do
      stubs(:results).returns(mc_res)
      stubs(:agent).returns('mc_stubbed_agent')
    end
    return mc_result
  end
end
