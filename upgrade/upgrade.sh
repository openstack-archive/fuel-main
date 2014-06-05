#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
PYTHONPATH=$SCRIPT_PATH/upgrade/site-packages $SCRIPT_PATH/upgrade/bin/fuel-upgrade --help
