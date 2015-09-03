#!/bin/bash

#    Copyright 2015 Mirantis, Inc.
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
# depends on environment settings


function execute() {
  if [ -n "$REMOTE_HOST" ]; then
    if [ -z "$REMOTE_PORT" ]; then
      ssh $REMOTE_HOST "${@//\ /\\ }"
    else
      ssh -p $REMOTE_PORT $REMOTE_HOST "${@//\ /\\ }"
    fi
  else
    eval "${@//\ /\\ }"
  fi
}

# copy file to remote machine if needed
# be careful, do nothing in case if file with same name exists on target machine
function copy_if_required() {
  source_path=$1
  if [ -n "$REMOTE_HOST" ]; then
    if ! execute test -f $source_path; then
      # the scripts always find iso in original path
      # reconstruct same path on remote machine
      source_dir=$(dirname $source_path)
      echo "Copying $source_path to $REMOTE_HOST:$source_path..."
      execute mkdir -p $source_dir && copy $source_path $source_path || exit 1
    else
      echo "Skip copying the file $source_path, it already exists on $REMOTE_HOST."
    fi
  fi
}


function copy() {
  src=$1
  dst=$2

  if [ -n "$REMOTE_HOST" ]; then
    if [ -z "$REMOTE_PORT" ]; then
      scp $src $REMOTE_HOST:$dst
    else
      scp -P $REMOTE_PORT $src $REMOTE_HOST:$dst
    fi
  else
    cp $src $dst
  fi
}
