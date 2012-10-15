$:.unshift File.expand_path('lib', File.dirname(__FILE__))
require 'astute'

Gem::Specification.new do |s|
  s.name = 'astute'
  s.version = Astute::VERSION

  s.summary = 'Orchestrator for OpenStack deployment'
  s.description = 'Orchestrator of deployment via Puppet & MCollective. Works both with Nailgun and from CLI.'
  s.authors = ['Mike Scherbakov']
  s.email   = ['mscherbakov@mirantis.com']

  s.add_dependency 'mcollective-client', '> 2.0.0'

  s.files   = Dir.glob("{bin,lib,spec}/**/*")
  s.executables = ['astute']
  s.require_path = 'lib'
end

