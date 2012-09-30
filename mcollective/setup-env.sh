#!/bin/bash
ln -sf `readlink -f agent/nailyfact.rb` /usr/share/mcollective/plugins/mcollective/agent/nailyfact.rb
ln -sf `readlink -f agent/nailyfact.ddl` /usr/share/mcollective/plugins/mcollective/agent/nailyfact.ddl
ln -sfT `readlink -f puppet/modules/nailytest` /etc/puppet/modules/nailytest
ln -sf `readlink -f puppet/manifests/site.pp` /etc/puppet/manifests/site.pp
restart mcollective
