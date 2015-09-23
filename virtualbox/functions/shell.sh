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

# This file contains the functions, those encapsulate executing of command.
# Each command might be executed on the local machine or on the remote machine
# depending on environment settings

shell_ssh_options=""
shell_scp_options=""

if [ -n "$REMOTE_PORT" ]; then
  shell_ssh_options="-p $REMOTE_PORT $shell_ssh_options"
  shell_scp_options="-P $REMOTE_PORT $shell_scp_options"
fi


function execute() {
  #  use shell substitution pattern ${parameter/pattern/string}, to escape spaces in arguments.
  if [ -n "$REMOTE_HOST" ]; then
    eval "ssh $shell_ssh_options $REMOTE_HOST \"${@//\ /\\ }\""
  else
    eval "${@//\ /\\ }"
  fi
}

# copy file to remote machine if needed
# be careful, do nothing in case if file with same name exists on target machine
function copy_if_required() {
  local source_path=$1
  if [ -n "$REMOTE_HOST" ]; then
    if ! execute test -f $source_path; then
      # the scripts always find iso in original path
      # reconstruct same path on remote machine
      local source_dir=$(dirname $source_path)
      echo "Copying $source_path to $REMOTE_HOST:$source_path..."
      execute mkdir -p $source_dir && copy $source_path $source_path || exit 1
    else
      echo "Skip copying the file $source_path, it already exists on $REMOTE_HOST."
    fi
  fi
}


function copy() {
  local src=$1
  local dst=$2

  if [ -n "$REMOTE_HOST" ]; then
    eval "scp $shell_scp_options $src $REMOTE_HOST:$dst"
  else
    cp $src $dst
  fi
}
