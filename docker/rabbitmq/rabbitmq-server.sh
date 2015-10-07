#!/bin/bash
function cleanup() {
    local pids=$(jobs -p)
    if [[ -n "$pids" ]]; then
        kill $pids >/dev/null 2>/dev/null
    fi
}
trap 'cleanup; sleep 5' EXIT

su rabbitmq -c /usr/lib/rabbitmq/bin/rabbitmq-server
