#!/bin/bash
for agent in `ls mcollective/agent/`; do
    echo "Linking agent $agent of mcollective.."
    ln -sf `readlink -f mcollective/agent/$agent` /usr/libexec/mcollective/mcollective/agent/$agent
done
ln -sfT `readlink -f puppet/modules/nailytest` /etc/puppet/modules/nailytest
ln -sf `readlink -f puppet/manifests/site.pp` /etc/puppet/manifests/site.pp
service mcollective restart
