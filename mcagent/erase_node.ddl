metadata    :name        => "Erase node bootloader",
            :description => "Erase node bootloader and reboot it.",
            :author      => "Andrey Danin",
            :license     => "MIT",
            :version     => "0.1",
            :url         => "http://mirantis.com",
            :timeout     => 40

action "erase_node", :description => "Zeroing of boot device" do
    display :always
end

action "reboot_node", :description => "Reboot node" do
    display :always
end
