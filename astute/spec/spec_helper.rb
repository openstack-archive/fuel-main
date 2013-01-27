$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'rspec'
# Following require is needed for rcov to provide valid results
require 'rspec/autorun'
require 'yaml'
require 'astute'

RSpec.configure do |config|
  config.mock_with :mocha
end

