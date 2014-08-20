#!/bin/bash

#    Copyright 2014 Mirantis, Inc.
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

# This file contains the functions to get available memory on host PC

get_available_memory() {
  os_type=$1
  local total_memory=""
  # Check available commands and RAM on host PC
  if [ "$os_type" = "linux" ]; then
    # runing on linux
    if [ "$(which free)" != "" ]; then
      # using free
      total_memory=$(free | grep Mem | awk '{print $2}')
    elif [ $(which top) != '' ]; then
      # using top
      total_memory=$(top -n 1 | grep "Mem:" | awk '{ print $4 }')
    else
      total_memory="-1"
    fi
  elif [ "$os_type" = "darwin" ]; then
    # runing on mac os darwin
    if [ "$(which sysctl)" != "" ]; then
      # using sysctl
      total_memory=$(sysctl -n hw.memsize)
      total_memory=$(( $total_memory / 1024 ))
    else
      total_memory="-1"
    fi
  elif [ "$os_type" = "cygwin" ]; then
    # runing on cygwin
    if [ "$(which free)" != "" ]; then
      # using free
      total_memory=$(free | grep Mem | awk '{print $2}')
    elif [ $(which top) != '' ]; then
      # using top
      total_memory=$(top -n 1 | grep "Mem:" | awk '{ print $4 }')
    else
      total_memory="-1"
    fi
  fi
  echo $total_memory
}