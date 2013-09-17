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

require 'astute'
require 'naily/version'
require 'naily/config'

require 'logger'
require 'json'

module Naily
  autoload 'Worker', 'naily/worker'
  autoload 'Server', 'naily/server'
  autoload 'Producer', 'naily/producer'
  autoload 'Dispatcher', 'naily/dispatcher'
  autoload 'Reporter', 'naily/reporter'
  autoload 'SubtaskReporter', 'naily/reporter'

  def self.logger
    @logger
  end

  def self.logger=(logger)
    Astute.logger = logger
    @logger       = logger
  end
end
