#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

# TODO: remove 'test -f' when I9d7428c9fc21c705a1aee7fbca8003829a81e1d0
# is merged
test -f /etc/puppet/modules/nailgun/examples/hiera-for-container.pp && \
  puppet apply -d -v /etc/puppet/modules/nailgun/examples/hiera-for-container.pp

puppet apply -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp
