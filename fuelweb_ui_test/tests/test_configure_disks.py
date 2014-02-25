import random
import time
from pageobjects.base import ConfirmPopup
from pageobjects.environments import Environments
from pageobjects.node_disks_settings import DisksSettings
from pageobjects.nodes import Nodes, RolesPanel, NodeInfo
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase


class TestConfigureDisks(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """Global precondition

        Steps:
            1. Create simple environment with default values
            2. Add one controller node
        """
        BaseTestCase.setUpClass()
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on created environment
            2. Select controller node
            3. Click Configure Disks
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().nodes[0].details.click()
        NodeInfo().edit_disks.click()
        time.sleep(1)

    def test_volume_animation(self):
        """Expand and collapse blocks with disk information

        Scenario:
            1. Click on disk area
            2. Verify that area is expanded and disk information is available
            3. Click disk area again
            4. Verify that area is collapsed and
               disk information is unavailable
        """
        with DisksSettings() as s:
            s.disks[0].volume_os.parent.click()
            time.sleep(1)
            self.assertTrue(
                s.disks[0].details_panel.is_displayed(),
                'details panel is expanded')

            s.disks[0].volume_os.parent.click()
            time.sleep(1)
            self.assertFalse(
                s.disks[0].details_panel.is_displayed(),
                'details panel is expanded')

    def test_remove_volume_cross(self):
        """Remove disk volume by clicking on X button

        Scenario:
            1. Click on disk area
            2. Click on X button for some volume group
            3. Verify that image size is 0 and there is Unallocated space
        """
        with DisksSettings() as s:
            s.disks[0].volume_image.parent.click()
            time.sleep(1)
            s.disks[0].volume_image.close_cross.click()
            self.assertFalse(
                s.disks[0].volume_image.close_cross.is_displayed(),
                'Image volume has been removed')
            self.assertEqual(
                '0',
                s.disks[0].volume_group_image.input.get_attribute('value'),
                'image volume size is 0')

    def test_use_all_allowed(self):
        """Use all allowed space

        Scenario:
            1. Click on disk area
            2. Click on X button for all volumes group
            3. Click Use all allowed space for Base system
            4. Verify that all space is allocated for Base system
            5. Remove all volumes group and click
               Use all allowed space for Image Storage
            6. Verify that all space is allocated for Image Storage
        """
        with DisksSettings() as s:
            s.disks[1].volume_image.parent.click()
            time.sleep(1)
            s.disks[1].volume_image.close_cross.click()
            unallocated = s.disks[1].volume_unallocated.size.text

            s.disks[1].volume_group_os.use_all.click()
            self.assertEqual(
                unallocated, s.disks[1].volume_os.size.text,
                'Base system uses all allowed space'
            )
            s.disks[1].volume_os.close_cross.click()

            s.disks[1].volume_group_image.use_all.click()
            self.assertEqual(
                unallocated, s.disks[1].volume_image.size.text,
                'Image storage uses all allowed space'
            )

    def test_type_volume_size(self):
        """Allocate space for volume groups

        Scenario:
            1. Click on disk area
            2. Allocate space for Image Storage
            3. Verify that allocated size is correct in the header of disk area
        """
        values = [random.randint(100000, 200000) for i in range(3)]
        with DisksSettings() as s:
            s.disks[0].volume_image.parent.click()
            time.sleep(1)
            for v in values:
                s.disks[0].volume_group_image.input.clear()
                s.disks[0].volume_group_image.input.send_keys(v)
                time.sleep(0.5)
                exp = '{0:.1f} GB'.format((float(v) / 1024))
                cur = s.disks[0].volume_image.size.text
                self.assertEqual(
                    exp, cur,
                    'Volume size. exp: {0} ({1}), cur {2}'.format(exp, v, cur))

    def test_save_load_defaults(self):
        """Load default values

        Scenario:
            1. Click on disk area
            2. Allocate space for Image Storage
            3. Apply changes
            4. Click Load Defaults
            5. Verify that Image size is default value
        """
        default = None
        value = random.randint(60000, 80000)
        with DisksSettings() as s:
            s.disks[0].volume_image.parent.click()
            time.sleep(1)
            default = s.disks[0].volume_group_image.input.\
                get_attribute('value')
            s.disks[0].volume_group_image.input.\
                clear()
            s.disks[0].volume_group_image.input.\
                send_keys(value)
            s.apply.click()
            time.sleep(1)
        self.refresh()
        with DisksSettings() as s:
            time.sleep(2)
            self.assertEqual(
                "{:,}".format(value),
                s.disks[0].volume_group_image.input.get_attribute('value'),
                'New value has been saved'
            )
            s.load_defaults.click()
            time.sleep(1)
            self.assertEqual(
                default,
                s.disks[0].volume_group_image.input.get_attribute('value'),
                'default value has been restored'
            )

    def test_cancel_changes(self):
        """Cancel changes to disk configuring

        Scenario:
            1. Click on disk area
            2. Allocate space for Image Storage
            3. Click Cancel Changes
            4. Verify that default value is restored
        """
        with DisksSettings() as s:
            s.disks[0].volume_image.parent.click()
            time.sleep(1)
            default = s.disks[0].volume_group_image.input.\
                get_attribute('value')
            s.disks[0].volume_group_image.input.\
                clear()
            s.disks[0].volume_group_image.input.\
                send_keys(random.randint(60000, 80000))
            s.cancel_changes.click()
            time.sleep(1)
            self.assertEqual(
                default,
                s.disks[0].volume_group_image.input.get_attribute('value'),
                'default value has been restored'
            )

    def test_confirm_if_back_to_list(self):
        """Back to node list form disk configuring

        Scenario:
            1. Click on disk area
            2. Allocate space for Image Storage
            3. Click Back to node list
            4. Click Stay on page
            5. Verify that changes aren't discarded
            6. Click Back to node list
            7. Click Leave page
            8. Verify that Nodes page is present and changes are discarded
        """
        with DisksSettings() as s:
            s.disks[0].volume_image.parent.click()
            time.sleep(1)
            s.disks[0].volume_group_image.input.\
                clear()
            s.disks[0].volume_group_image.input.\
                send_keys('0')

            s.back_to_node_list.click()
            with ConfirmPopup() as p:
                p.stay_on_page.click()
                p.wait_until_exists()
            self.assertEqual(
                '0', s.disks[0].volume_group_image.
                input.get_attribute('value'),
                'Value is not changed')

            s.back_to_node_list.click()
            with ConfirmPopup() as p:
                p.leave_page.click()
                p.wait_until_exists()
                time.sleep(1)

            self.assertTrue(
                Nodes().add_nodes.is_displayed(),
                'Backed to nodes page. Add Nodes button is displayed')

    def test_configure_disks_of_several_nodes(self):
        """Configure disks for several nodes

        Scenario:
            1. Add two compute nodes
            2. Select this two nodes and click configure disks
            3. Allocate size for Base system volume
            4. Click apply changes
            5. Verify that changes are correctly applied
        """
        values = [random.randint(100000, 500000) for i in range(4)]

        # Go back to nodes page
        Tabs().nodes.click()
        time.sleep(1)
        # Add second node
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().select_all_in_group[1].click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        # change volumes size
        with Nodes() as n:
            n.select_all_in_group[1].click()
            n.configure_disks.click()
            time.sleep(1)

        with DisksSettings() as s:
            for i, v in enumerate(values):
                s.disks[i].volume_storage.parent.click()
                time.sleep(1)
                s.disks[i].volume_group_storage.input.\
                    clear()
                s.disks[i].volume_group_storage.input.\
                    send_keys(v)
            s.apply.click()
            time.sleep(1)

        for i in range(1, 3):
            # Go to nodes page
            Tabs().nodes.click()
            time.sleep(1)
            # Verify disks settings of each node
            Nodes().nodes[i].details.click()
            NodeInfo().edit_disks.click()
            time.sleep(1)

            for j, v in enumerate(values):
                self.assertEqual(
                    "{:,}".format(v),
                    s.disks[j].volume_group_storage.input.
                    get_attribute('value'),
                    'Image volume size of disk {0} of node {0} is correct'.
                    format(j, i))
