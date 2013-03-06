#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe Astute::Node do
  it "accepts hash for initialization" do
    node = Astute::Node.new('uid' => 'abc', 'info' => 'blabla')
    node.uid.should == 'abc'
    node.info.should == 'blabla'
  end

  it "requires uid" do
    expect{ Astute::Node.new({}) }.to raise_error(TypeError)
  end

  it "stringifies uid" do
    node = Astute::Node.new('uid' => :abc)
    node.uid.should == 'abc'
    node = Astute::Node.new('uid' => 123)
    node.uid.should == '123'
  end

  it "denies uid changes" do
    node = Astute::Node.new('uid' => 1)
    expect{ node.uid    = 2 }.to raise_error(TypeError)
    expect{ node['uid'] = 2 }.to raise_error(TypeError)
    expect{ node[:uid]  = 2 }.to raise_error(TypeError)
  end

  it "allows [] accessors" do
    node = Astute::Node.new('uid' => 123, 'info' => 'abc')
    node['info'].should  == 'abc'
    node[:info].should   == 'abc'
    node['info']          = 'cba'
    node['info'].should  == 'cba'
    node[:info]           = 'dcb'
    node[:info].should   == 'dcb'
  end

  it "unwraps to hash" do
    hash = {'uid' => '123', 'info' => 'abc'}
    node = Astute::Node.new(hash)
    node.to_hash.should == hash
    node.to_hash.should_not === node.instance_variable_get(:@table)
  end
end

describe Astute::NodesHash do
  it "accepts array of hashes or nodes for initialization and allows accessing by uid" do
    nodes = Astute::NodesHash.build([{'uid' => 123, 'info' => 'blabla1'}, Astute::Node.new({'uid' => 'abc', 'info' => 'blabla2'})])
    nodes['123'].info.should == 'blabla1'
    nodes['abc'].info.should == 'blabla2'
    nodes[123].info.should == 'blabla1'
    nodes[:abc].info.should == 'blabla2'
    nodes['123'].uid.should == '123'
    nodes.values.map(&:class).uniq.should == [Astute::Node]
  end

  it "allows easy elements addition and normalizes data" do
    nodes = Astute::NodesHash.new
    nodes << {'uid' => 1} << {'uid' => 2}
    nodes.push({'uid' => 3}, {'uid' => 4}, {'uid' => 5})
    nodes.keys.sort.should == %w(1 2 3 4 5)
    nodes.values.map(&:class).uniq.should == [Astute::Node]
  end

  it "introduces meaningful aliases" do
    nodes = Astute::NodesHash.build([{'uid' => 123, 'info' => 'blabla1'}, Astute::Node.new({'uid' => 'abc', 'info' => 'blabla2'})])
    nodes.uids.should  == nodes.keys
    nodes.nodes.should == nodes.values
  end

  it "denies direct accessors" do
    expect{ Astute::NodesHash.new['fake-uid'] = {'bla' => 'bla'} }.to raise_error(NoMethodError)
  end
end