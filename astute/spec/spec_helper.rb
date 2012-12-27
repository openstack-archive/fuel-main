$LOAD_PATH << File.join(File.dirname(__FILE__),"..","lib")
require 'rspec'
require 'astute'

RSpec.configure do |config|
  config.mock_with :mocha
end

