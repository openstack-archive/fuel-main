#!/bin/bash
# NOTE(mihgen): This script is created for development purposes
chef-solo -l debug -c solo.rb -j solo.json
