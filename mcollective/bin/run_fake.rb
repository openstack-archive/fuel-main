$LOAD_PATH << '../'

require 'client/client'

tc = TestClient.new

tc.discover
tc.run
tc.report
tc.disconnect
