#!/usr/bin/env rspec
require File.join(File.dirname(__FILE__), "..", "spec_helper")

describe "NailyFact DeploymentEngine" do
  context "When deploy is called, " do
    before(:each) do
      @ctx = mock
      @ctx.stubs(:task_id)
      @ctx.stubs(:deploy_log_parser).returns(Astute::LogParser::NoParsing.new)
      reporter = mock
      @ctx.stubs(:reporter).returns(reporter)
      reporter.stubs(:report)
      @deploy_engine = Astute::DeploymentEngine::NailyFact.new(@ctx)
      @data = {"args" =>
                {"attributes" =>
                  {"storage_network_range" => "172.16.0.0/24", "auto_assign_floating_ip" => false,
                   "mysql" => {"root_password" => "Z2EqsZo5"},
                   "keystone" => {"admin_token" => "5qKy0i63", "db_password" => "HHQ86Rym", "admin_tenant" => "admin"},
                   "nova" => {"user_password" => "h8RY8SE7", "db_password" => "Xl9I51Cb"},
                   "glance" => {"user_password" => "nDlUxuJq", "db_password" => "V050pQAn"},
                   "rabbit" => {"user" => "nova", "password" => "FLF3txKC"},
                   "management_network_range" => "192.168.0.0/24",
                   "public_network_range" => "240.0.1.0/24",
                   "fixed_network_range" => "10.0.0.0/24",
                   "floating_network_range" => "240.0.0.0/24"},
               "task_uuid" => "19d99029-350a-4c9c-819c-1f294cf9e741",
               "nodes" => [{"mac" => "52:54:00:0E:B8:F5", "status" => "provisioning",
                            "uid" => "devnailgun.mirantis.com", "error_type" => nil,
                            "fqdn" => "devnailgun.mirantis.com",
                            "network_data" => [{"gateway" => "192.168.0.1",
                                                "name" => "management", "dev" => "eth0",
                                                "brd" => "192.168.0.255", "netmask" => "255.255.255.0",
                                                "vlan" => 102, "ip" => "192.168.0.2/24"},
                                               {"gateway" => "240.0.1.1",
                                                "name" => "public", "dev" => "eth0",
                                                "brd" => "240.0.1.255", "netmask" => "255.255.255.0",
                                                "vlan" => 101, "ip" => "240.0.1.2/24"},
                                               {"name" => "floating", "dev" => "eth0", "vlan" => 120},
                                               {"name" => "fixed", "dev" => "eth0", "vlan" => 103},
                                               {"name" => "storage", "dev" => "eth0", "vlan" => 104}],
                            "id" => 1,
                            "ip" => "10.20.0.200",
                            "role" => "controller"},
                           {"mac" => "52:54:00:50:91:DD", "status" => "provisioning",
                            "uid" => 2, "error_type" => nil,
                            "fqdn" => "slave-2.mirantis.com",
                            "network_data" => [{"gateway" => "192.168.0.1",
                                                "name" => "management", "dev" => "eth0",
                                                "brd" => "192.168.0.255", "netmask" => "255.255.255.0",
                                                "vlan" => 102, "ip" => "192.168.0.3/24"},
                                               {"gateway" => "240.0.1.1",
                                                "name" => "public", "dev" => "eth0",
                                                "brd" => "240.0.1.255", "netmask" => "255.255.255.0",
                                                "vlan" => 101, "ip" => "240.0.1.3/24"},
                                               {"name" => "floating", "dev" => "eth0", "vlan" => 120},
                                               {"name" => "fixed", "dev" => "eth0", "vlan" => 103},
                                               {"name" => "storage", "dev" => "eth0", "vlan" => 104}],
                            "id" => 2,
                            "ip" => "10.20.0.221",
                            "role" => "compute"},
                           {"mac" => "52:54:00:C3:2C:28", "status" => "provisioning",
                            "uid" => 3, "error_type" => nil,
                            "fqdn" => "slave-3.mirantis.com",
                            "network_data" => [{"gateway" => "192.168.0.1",
                                                "name" => "management", "dev" => "eth0",
                                                "brd" => "192.168.0.255", "netmask" => "255.255.255.0",
                                                "vlan" => 102, "ip" => "192.168.0.4/24"},
                                               {"gateway" => "240.0.1.1",
                                                "name" => "public", "dev" => "eth0",
                                                "brd" => "240.0.1.255", "netmask" => "255.255.255.0",
                                                "vlan" => 101, "ip" => "240.0.1.4/24"},
                                               {"name" => "floating", "dev" => "eth0", "vlan" => 120},
                                               {"name" => "fixed", "dev" => "eth0", "vlan" => 103},
                                               {"name" => "storage", "dev" => "eth0", "vlan" => 104}],
                            "id" => 3,
                            "ip" => "10.20.0.68",
                            "role" => "compute"}]},
              "method" => "deploy",
              "respond_to" => "deploy_resp"}
      ha_nodes = @data['args']['nodes'] +
                          [{"mac" => "52:54:00:0E:88:88", "status" => "provisioned",
                            "uid" => "4", "error_type" => nil,
                            "fqdn" => "controller-4.mirantis.com",
                            "network_data" => [{"gateway" => "192.168.0.1",
                                                "name" => "management", "dev" => "eth0",
                                                "brd" => "192.168.0.255", "netmask" => "255.255.255.0",
                                                "vlan" => 102, "ip" => "192.168.0.5/24"},
                                               {"gateway" => "240.0.1.1",
                                                "name" => "public", "dev" => "eth0",
                                                "brd" => "240.0.1.255", "netmask" => "255.255.255.0",
                                                "vlan" => 101, "ip" => "240.0.1.5/24"},
                                               {"name" => "floating", "dev" => "eth0", "vlan" => 120},
                                               {"name" => "fixed", "dev" => "eth0", "vlan" => 103},
                                               {"name" => "storage", "dev" => "eth0", "vlan" => 104}],
                            "id" => 4,
                            "ip" => "10.20.0.205",
                            "role" => "controller"},
                           {"mac" => "52:54:00:0E:99:99", "status" => "provisioned",
                            "uid" => "5", "error_type" => nil,
                            "fqdn" => "controller-5.mirantis.com",
                            "network_data" => [{"gateway" => "192.168.0.1",
                                                "name" => "management", "dev" => "eth0",
                                                "brd" => "192.168.0.255", "netmask" => "255.255.255.0",
                                                "vlan" => 102, "ip" => "192.168.0.6/24"},
                                               {"gateway" => "240.0.1.1",
                                                "name" => "public", "dev" => "eth0",
                                                "brd" => "240.0.1.255", "netmask" => "255.255.255.0",
                                                "vlan" => 101, "ip" => "240.0.1.6/24"},
                                               {"name" => "floating", "dev" => "eth0", "vlan" => 120},
                                               {"name" => "fixed", "dev" => "eth0", "vlan" => 103},
                                               {"name" => "storage", "dev" => "eth0", "vlan" => 104}],
                            "id" => 5,
                            "ip" => "10.20.0.206",
                            "role" => "controller"}]
      @data_ha = Marshal.load(Marshal.dump(@data))
      @data_ha['args']['nodes'] = ha_nodes
      @data_ha['args']['attributes']['deployment_mode'] = "ha"
      # VIPs are required for HA mode and should be passed from Nailgun (only in HA)
      @data_ha['args']['attributes']['management_vip'] = "192.168.0.111"
      @data_ha['args']['attributes']['public_vip'] = "240.0.1.111"
    end

    it "it should call valid method depends on attrs" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'ha'}
      attrs_modified = attrs.merge({'some' => 'somea'})
      
      @deploy_engine.expects(:attrs_ha).with(nodes, attrs).returns(attrs_modified)
      @deploy_engine.expects(:deploy_ha).with(nodes, attrs_modified)
      # All implementations of deploy_piece go to subclasses
      @deploy_engine.respond_to?(:deploy_piece).should be_true
      @deploy_engine.deploy(nodes, attrs)
    end

    it "it should raise an exception if deployment mode is unsupported" do
      nodes = [{'uid' => 1}]
      attrs = {'deployment_mode' => 'unknown'}
      expect {@deploy_engine.deploy(nodes, attrs)}.to raise_exception(/Method attrs_unknown is not implemented/)
    end

    it "multinode deploy should not raise any exception" do
      @data['args']['attributes']['deployment_mode'] = "multinode"
      Astute::Metadata.expects(:publish_facts).times(@data['args']['nodes'].size)
      # we got two calls, one for controller, and another for all computes
      controller_nodes = @data['args']['nodes'].select{|n| n['role'] == 'controller'}
      compute_nodes = @data['args']['nodes'].select{|n| n['role'] == 'compute'}
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes, instance_of(Fixnum), true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, compute_nodes, instance_of(Fixnum), true).once
      @deploy_engine.deploy(@data['args']['nodes'], @data['args']['attributes'])
    end

    it "ha deploy should not raise any exception" do
      Astute::Metadata.expects(:publish_facts).at_least_once
      controller_nodes = @data_ha['args']['nodes'].select{|n| n['role'] == 'controller'}
      compute_nodes = @data_ha['args']['nodes'].select{|n| n['role'] == 'compute'}
      controller_nodes.each do |n|
        Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [n], 0, false).once
      end
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes, 0, false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, [controller_nodes.first], 0, false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes, 0, false).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, controller_nodes, 3, true).once
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, compute_nodes, instance_of(Fixnum), true).once
      @deploy_engine.deploy(@data_ha['args']['nodes'], @data_ha['args']['attributes'])
    end

    it "ha deploy should not raise any exception if there are only one controller" do
      Astute::Metadata.expects(:publish_facts).at_least_once
      Astute::PuppetdDeployer.expects(:deploy).times(5)
      ctrl = @data_ha['args']['nodes'].select {|n| n['role'] == 'controller'}[0]
      @deploy_engine.deploy([ctrl], @data_ha['args']['attributes'])
    end

    it "singlenode deploy should not raise any exception" do
      @data['args']['attributes']['deployment_mode'] = "singlenode"
      @data['args']['nodes'] = [@data['args']['nodes'][0]]  # We have only one node in singlenode
      Astute::Metadata.expects(:publish_facts).times(@data['args']['nodes'].size)
      Astute::PuppetdDeployer.expects(:deploy).with(@ctx, @data['args']['nodes'], instance_of(Fixnum), true).once
      @deploy_engine.deploy(@data['args']['nodes'], @data['args']['attributes'])
    end
  end
end
