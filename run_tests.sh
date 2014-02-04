#!/bin/bash

make -n && flake8 --ignore=H302,H802 --exclude bin/,include/,lib/,local/,tmp/ fuelweb_test
