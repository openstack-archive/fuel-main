#!/bin/bash
for agent in `ls mcollective/agent/`; do
    echo "Linking agent $agent of mcollective.."
    ln -sf `readlink -f mcollective/agent/$agent` /usr/libexec/mcollective/mcollective/agent/$agent
done
ln -sfT `readlink -f puppet/modules/nailytest` /etc/puppet/modules/nailytest
ln -sf `readlink -f puppet/manifests/site.pp` /etc/puppet/manifests/site.pp
ln -sf `readlink -f ../bootstrap/sync/usr/bin/net_probe.py` /usr/bin/net_probe.py
uuidgen > /etc/bootif  # for net_probe plugin
service mcollective restart
