#!/bin/bash

echo ''
echo "Collecting debug data from host"
echo ''

echo "========== DOCKER INFO ================="
sudo docker info
echo "========================================"


echo "============= DMESG OUTPUT ============="
dmesg | grep -iE '(assert|segfault)'`
echo "========================================"

