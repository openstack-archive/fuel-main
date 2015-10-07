#!/bin/bash
function cleanup() {
    local pids
    for pid in $(jobs -p); do
        kill $pids >/dev/null 2>/dev/null
    done
    for t in 5 1 1 1; do
        sleep $t
        pkill -u rabbitmq >/dev/null 2>/dev/null
    done
    sleep 5
}
trap cleanup EXIT
su rabbitmq -l -c /usr/lib/rabbitmq/bin/rabbitmq-server