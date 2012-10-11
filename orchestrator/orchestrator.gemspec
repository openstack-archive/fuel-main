$:.unshift File.expand_path('lib', File.dirname(__FILE__))
require 'orchestrator'

Gem::Specification.new do |s|
  s.name = 'orchestrator'
  s.version = Orchestrator::VERSION

  s.summary = 'Orchestrator for OpenStack deployment'
  s.description = 'Orchestrator of deployment via Puppet & MCollective. Works both with Nailgun and from CLI.'
  s.authors = ['Mike Scherbakov']
  s.email   = ['mscherbakov@mirantis.com']

  s.add_dependency 'mcollective-client', '> 2.0.0'

  s.files   = Dir.glob("{bin,lib,spec}/**/*")
  s.executables = ['orchestrator']
  s.require_path = 'lib'
end

