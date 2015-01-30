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
local total_memory
  case $(uname) in
    Linux | CYGWIN*)
      total_memory=$(LANG=C free | grep Mem | awk '{print $2}')
    ;;
    Darwin)
      total_memory=$(sysctl -n hw.memsize)
      total_memory=$(( $total_memory / 1024 ))
    ;;
    *)
      total_memory="-1"
    ;;
  esac
  echo $total_memory
}
