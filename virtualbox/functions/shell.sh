#!/bin/bash

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# This file contains the functions for abstracting over running command over ssh or directly
# depends on start configuration


function execute() {
  if [ -n "$REMOTE_HOST" ]; then
    ssh $REMOTE_HOST "${@//\ /\\ }"
  else
    eval "${@//\ /\\ }"
  fi
}


# copy file to remote machine if needed
# be careful, do nothing in case if file with same name exists on target machine
function copy_file() {
  source_path=$1
  if [ -n "$REMOTE_HOST" ]; then
    if ! ssh $REMOTE_HOST test -f $source_path; then
      # the scripts always find iso in original path
      # reconstruct same path on remote machine
      source_dir=$(dirname $source_path)
      echo "Copying $source_path to $REMOTE_HOST:$source_path..."
      ssh $REMOTE_HOST mkdir -p $source_dir && scp $source_path $REMOTE_HOST:$source_path || exit 1;
    else
      echo "Skip copying the file $source_path, it already exists on $REMOTE_HOST."
    fi
  fi
}
