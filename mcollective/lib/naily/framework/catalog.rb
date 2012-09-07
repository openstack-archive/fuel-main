require 'puppet'
require 'puppet/node'
require 'yaml'
require 'json'
require 'pp'
require 'logger'
require 'puppet/parser/compiler'
require 'puppet/indirector/yaml'
require 'puppet/indirector/request'
require 'puppet/indirector/node/exec'
require 'puppet/indirector/catalog/yaml'
require 'puppet/application'
require 'puppet/external/pson/common'

module Naily
  module Framework
    module Catalog
      class Yaml < Puppet::Node::Exec

        def initialize basepath
          @basepath = basepath
        end

        def find(request)
          if File.exist? path(request.key)
            output = open(path(request.key)) do |file|
              file.read
            end
          else
            raise "File #{path(request.key)} does not exist"
          end

          # Translate the output to ruby.
          result = translate(request.key, output)
          
          create_node(request.key, result)
        end

        # This method is the same as that one in super class excluding
        # that the facts are not merged into node
        def create_node(name, result)
          node = Puppet::Node.new(name)
          set = false
          [:parameters, :classes, :environment].each do |param|
            if value = result[param]
              node.send(param.to_s + "=", value)
              set = true
            end
          end
          
          node
        end

        def path name, ext=".yaml"
          File.join(@basepath, name + ext)
        end
        
      end

      
      def self.get_catalog basepath, nodename
        
        request = Puppet::Indirector::Request.new('node', :find, nodename)
        
        node_terminus = Yaml.new basepath
        node = node_terminus.find(request)

        compiler = Puppet::Parser::Compiler.new(node)

        catalog = compiler.compile
        catalog_json = PSON::generate(catalog.to_resource, 
                                      :allow_nan => true, 
                                      :max_nesting => false)
        
        # jj JSON.load(catalog_json)
      end
    end
  end
end
