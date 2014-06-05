#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
PYTHONPATH=$SCRIPT_PATH/site-packages $SCRIPT_PATH/bin/fuel-upgrade --help
