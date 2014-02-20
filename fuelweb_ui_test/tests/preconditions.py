import time
from pageobjects.environments import Environments, Wizard, DeployChangesPopup
from pageobjects.header import TaskResultAlert
from pageobjects.nodes import Nodes, RolesPanel
from settings import OPENSTACK_CENTOS, OPENSTACK_RELEASE_CENTOS
from tests.base import BaseTestCase


class Environment:

    @staticmethod
    def simple_flat(name=OPENSTACK_CENTOS,
                    release=OPENSTACK_RELEASE_CENTOS):
        BaseTestCase.get_home()
        Environments().create_cluster_box.click()
        with Wizard() as w:
            w.name.send_keys(name)
            w.release.select_by_visible_text(release)
            for i in range(6):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

    @staticmethod
    def ha_flat(name=OPENSTACK_CENTOS,
                release=OPENSTACK_RELEASE_CENTOS):
        BaseTestCase.get_home()
        Environments().create_cluster_box.click()
        with Wizard() as w:
            w.name.send_keys(name)
            w.release.select_by_visible_text(release)
            w.next.click()
            w.mode_ha_compact.click()
            for i in range(5):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

    @staticmethod
    def simple_neutron_gre(name=OPENSTACK_CENTOS,
                           release=OPENSTACK_RELEASE_CENTOS):
        BaseTestCase.get_home()
        Environments().create_cluster_box.click()
        with Wizard() as w:
            w.name.send_keys(name)
            w.release.select_by_visible_text(release)
            for i in range(3):
                w.next.click()
            w.network_neutron_gre.click()
            for i in range(3):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

    @staticmethod
    def deploy_nodes(controllers=0, computes=0, cinders=0, cephs=0):
        def add(role, amount):
            if amount < 1:
                return

            Nodes().add_nodes.click()
            time.sleep(1)
            for i in range(amount):
                Nodes().nodes_discovered[i].checkbox.click()
            getattr(RolesPanel(), role).click()
            Nodes().apply_changes.click()
            time.sleep(1)

        add('controller', controllers)
        add('compute', computes)
        add('cinder', cinders)
        add('ceph_osd', cephs)

        time.sleep(1)
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
