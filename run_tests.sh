#!/bin/bash

set -e
set -x

flake8 --ignore=H301,H302,H306,H802 --exclude bin/,include/,lib/,local/,tmp/ --show-source fuelweb_test fuelweb_ui_test

