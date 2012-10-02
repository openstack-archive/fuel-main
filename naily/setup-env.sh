#!/bin/bash
for agent in `ls agent/`; do
    echo "Linking agent $agent of mcollective.."
    ln -sf `readlink -f agent/$agent` /usr/share/mcollective/plugins/mcollective/agent/$agent
done
ln -sfT `readlink -f puppet/modules/nailytest` /etc/puppet/modules/nailytest
ln -sf `readlink -f puppet/manifests/site.pp` /etc/puppet/manifests/site.pp
restart mcollective
