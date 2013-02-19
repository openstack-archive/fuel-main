metadata    :name        => "Network Probe Agent",
            :description => "Check network connectivity between nodes.",
            :author      => "Andrey Danin",
            :license     => "MIT",
            :version     => "0.1",
            :url         => "http://mirantis.com",
            :timeout     => 300

action "start_frame_listeners", :description => "Starts catching packets on interfaces" do
    display :always
end

action "send_probing_frames", :description => "Sends packets with VLAN tags" do
    display :always
end

action "get_probing_info", :description => "Get info about packets catched" do
    display :always
end

action "stop_frame_listeners", :description => "Stop catching packets, dump data to file" do
    display :always
end

action "echo", :description => "Silly echo" do
    display :always
end
