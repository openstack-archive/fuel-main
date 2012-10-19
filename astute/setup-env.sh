#!/bin/bash
for agent in `ls ../mcagent/`; do
    echo "Linking agent $agent of mcollective.."
    ln -sf `readlink -f ../mcagent/$agent` /usr/libexec/mcollective/mcollective/agent/$agent
done
ln -sfT `readlink -f ../puppet/nailytest` /etc/puppet/modules/nailytest
ln -sf `readlink -f ../puppet/nailytest/examples/site.pp` /etc/puppet/manifests/site.pp
ln -sf `readlink -f ../bootstrap/sync/usr/bin/net_probe.py` /usr/bin/net_probe.py
uuidgen > /etc/bootif  # for net_probe plugin
service mcollective restart
