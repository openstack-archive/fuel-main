#!/bin/bash

make -n && flake8 --ignore=H302,H802 fuelweb_test
