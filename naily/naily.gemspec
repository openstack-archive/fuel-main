$:.unshift File.expand_path('lib', File.dirname(__FILE__))

require 'naily/version'

Gem::Specification.new do |s|
  s.name = 'naily'
  s.version = Naily::VERSION

  s.summary = 'Backend server for Nailgun'
  s.description = 'Nailgun deployment job server'
  s.authors = ['Maxim Kulkin']
  s.email   = ['mkulkin@mirantis.com']

  s.add_dependency 'daemons'
  s.add_dependency 'amqp'
  s.add_dependency 'symboltable', '>= 1.0.2'
  s.add_dependency 'astute'

  s.files   = Dir.glob("{bin,lib}/**/*")
  s.executables = ['nailyd']
  s.require_path = 'lib'
end

