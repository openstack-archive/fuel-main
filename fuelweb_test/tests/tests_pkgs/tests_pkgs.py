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

import re

from proboscis import test
from proboscis.asserts import assert_equal

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger

import urllib2
import zlib
from xml.etree import ElementTree
from fuelweb_test import settings


@test(groups=["tests_pkgs"])
class CustomRepoTest (TestBasic):

    def __init__(self):
        TestBasic.__init__(self)
        self.path_scripts = './fuelweb_test/tests/tests_pkgs/'
        self.remote_path_scripts = '/tmp/'
        self.ubuntu_script = 'regenerate_ubuntu_repo'
        self.centos_script = 'regenerate_centos_repo'
        self.epel_release = 'http://download.fedoraproject.org/pub/epel/6'\
                            '/x86_64/epel-release-6-8.noarch.rpm'
        self.local_mirror_ubuintu = '/var/www/nailgun/ubuntu/fuelweb/x86_64'
        self.local_mirror_centos = '/var/www/nailgun/centos/fuelweb/x86_64'
        self.ubuntu_yaml_versions = '/etc/puppet/manifests/'\
                                    'ubuntu-versions.yaml'
        self.centos_yaml_versions = '/etc/puppet/manifests/'\
                                    'centos-versions.yaml'
        self.centos_supported_archs = ['noarch', 'x86_64']
        self.custom_pkgs_mirror = settings.CUSTOM_PKGS_MIRROR.strip()
        self.ready_snapshot = settings.SNAPSHOT.split(",")[0]

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["prepare_repository"])
    @log_snapshot_on_error
    def prepare_repository(self):
        """Prepare admin node to testing packages

        Scenario:
            1. Revert clean snapshot (ready_with_3_slaves by default)
            2. Install tools to manage deb/rpm repositories
            3. Download packages from testing repository
            4. Re-generate local repository via downloaded tools
            5. Make 'prepared_*' snapshot for running further tests

        Snapshot: "prepared_{}".format(self.ready_snapshot)

        """
        # Check necessary settings and revert a snapshot
        if not self.custom_pkgs_mirror:
            logger.info('No mirror has specified!')
            raise
        if not self.ready_snapshot:
            logger.info('No snapshot specified!')
            self.ready_snapshot = "ready_with_3_slaves"
            logger.info('Assuming snapshot name as "{}"'
                        ''.format(self.ready_snapshot))
        if not self.env.get_virtual_environment()\
                .has_snapshot(self.ready_snapshot):
            logger.info('There is no snapshot with the name: {}'
                        ''.format(self.ready_snapshot))
            raise

        self.env.revert_snapshot(self.ready_snapshot)

        # Pre-install tools for repository management.
        # TODO: is it be better if these packages be included
        #       into ISO at the building time?
        #       There was an issue with failed test when one of
        #       the following packages hasn't been downloaded.
        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            if (self.env.admin_install_pkg(self.epel_release)):
                logger.info('Cannot add "epel" repository on admin node.')
                raise
            else:
                master_pkgs = ['dpkg', 'dpkg-devel']
        else:
            master_pkgs = ['createrepo']

        for master_pkg in master_pkgs:
            if (self.env.admin_install_pkg(master_pkg)):
                logger.info('Cannot install package {0} on admin node.'
                            ''.format(master_pkg))
                raise

        # Uploading scripts that prepare local repositories:
        # 'regenerate_centos_repo' and 'regenerate_ubuntu_repo'
        try:
            remote = self.env.get_admin_remote()
            remote.upload('{0}/{1}'.format(self.path_scripts,
                                           self.ubuntu_script),
                          self.remote_path_scripts)
            remote.upload('{0}/{1}'.format(self.path_scripts,
                                           self.centos_script),
                          self.remote_path_scripts)
            remote.execute('chmod 755 {0}/{1}'.format(self.remote_path_scripts,
                                                      self.ubuntu_script))
            remote.execute('chmod 755 {0}/{1}'.format(self.remote_path_scripts,
                                                      self.centos_script))
        except Exception:
            logger.error("Could not upload scripts for update repositories.")
            raise

        # Creating a list of packages from the additional mirror
        pkgs_list = []
        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            url = "{}/Packages".format(self.custom_pkgs_mirror)
            try:
                pkgs_release = urllib2.urlopen(url).read()
            except (urllib2.HTTPError, urllib2.URLError) as e:
                logger.error(e)

            packages = (pkg for pkg in pkgs_release.split("\n\n") if pkg)
            for package in packages:
                upkg = {pstr.split()[0].lower(): ''.join(pstr.split()[1:])
                        for pstr in package.split("\n") if pstr[0].strip()}
                #if (upkg.has_key("package:") and
                #    upkg.has_key("version:") and
                #    upkg.has_key("filename:")):
                if (("package:" in upkg) and
                        ("version:" in upkg) and
                        ("filename:" in upkg)):
                    #TODO: add dependences list to upkg
                    pkgs_list.append(upkg)
                else:
                    logger.info('Missing one of the statement "Package:", '
                                '"Version:" or "Filename:" in {0}'.format(url))
                    raise

        else:
            url = "{}/repodata/repomd.xml".format(self.custom_pkgs_mirror)
            try:
                repomd_data = urllib2.urlopen(url).read()
            except (urllib2.HTTPError, urllib2.URLError) as e:
                logger.error(e)
            # Remove namespace attribute before parsing XML
            repomd_data = re.sub(' xmlns="[^"]+"', '', repomd_data, count=1)
            tree_repomd_data = ElementTree.fromstring(repomd_data)

            lists_location = ''
            for repomd in tree_repomd_data.findall('data'):
                if repomd.get('type') == 'primary':
                    repomd_location = repomd.find('location')
                    lists_location = repomd_location.get('href')
            if not lists_location:
                logger.info('CentOS mirror error: Could not parse {}'
                            ''.format(url))
                raise

            url = "{0}/{1}".format(self.custom_pkgs_mirror, lists_location)
            try:
                lists_data = urllib2.urlopen(url).read()
            except (urllib2.HTTPError, urllib2.URLError) as e:
                logger.error(e)
            if '.xml.gz' in lists_location:
                try:
                    d = zlib.decompressobj(zlib.MAX_WBITS | 32)
                    lists_data = d.decompress(lists_data)
                except Exception:
                    logger.info('CentOS mirror error: Could not decompress {}'
                                ''.format(url))
                    raise

            # Remove namespace attribute before parsing XML
            lists_data = re.sub(' xmlns="[^"]+"', '', lists_data, count=1)

            tree_lists_data = ElementTree.fromstring(lists_data)

            for flist in tree_lists_data.findall('package'):
                if flist.get('type') == 'rpm':
                    flist_arch = flist.find('arch').text
                    if flist_arch in self.centos_supported_archs:
                        flist_name = flist.find('name').text
                        flist_location = flist.find('location')
                        flist_file = flist_location.get('href')
                        flist_version = flist.find('version')
                        flist_ver = '{0}-{1}'.format(flist_version.get('ver'),
                                                     flist_version.get('rel'))
                        cpkg = {'package:': flist_name,
                                'version:': flist_ver,
                                'filename:': flist_file}
                        #TODO: add dependences list to cpkg
                        pkgs_list.append(cpkg)

        # Process the packages list:
        remote = self.env.get_admin_remote()

        # Set the local router as nameserver that will allow
        # the admin node to access the Mirantis osci repositories.
        dns_server = self.env.router()
        logger.info('echo "nameserver {0}" >> /etc/resolv.conf'
                    ''.format(dns_server))
        echo_result = remote.execute('echo "nameserver {0}" > /etc/resolv.conf'
                                     ''.format(dns_server))
        assert_equal(0, echo_result['exit_code'])

        for pkg in pkgs_list:
            #TODO: Previous versions of the updating packages must be removed
            # to avoid unwanted packet manager dependences resolution
            # (when some package still depends on other package which
            # is not going to be installed)

            logger.info('Downloading package: {0}/{1}'
                        ''.format(self.custom_pkgs_mirror, pkg["filename:"]))
            if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
                wget_cmd = "wget --directory-prefix {0}/pool/main/ {1}/{2}"\
                           .format(self.local_mirror_ubuintu,
                                   self.custom_pkgs_mirror,
                                   pkg["filename:"])
            else:
                wget_cmd = "wget --directory-prefix {0}/Packages/ {1}/{2}"\
                           .format(self.local_mirror_centos,
                                   self.custom_pkgs_mirror,
                                   pkg["filename:"])
            wget_result = remote.execute(wget_cmd)
            assert_equal(0, wget_result['exit_code'])

            #Update the corresponding .yaml with the new package version.
            if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
                yaml_versions = self.ubuntu_yaml_versions
            else:
                yaml_versions = self.centos_yaml_versions

            result = remote.execute('grep -e "^{0}: " {1}'
                                    ''.format(pkg["package:"], yaml_versions))
            if result['exit_code'] == 0:
                sed_cmd = 'sed -i \'s/^{0}: .*/{0}: "{1}"/\' {2}'\
                          .format(pkg["package:"],
                                  pkg["version:"],
                                  yaml_versions)
                sed_result = remote.execute(sed_cmd)
                assert_equal(0, sed_result['exit_code'])
            else:
                if result['exit_code'] == 1:
                    echo_cmd = 'echo "{0}: \\"{1}\\"" >> {2}'\
                               .format(pkg["package:"],
                                       pkg["version:"],
                                       yaml_versions)
                    echo_result = remote.execute(echo_cmd)
                    assert_equal(0, echo_result['exit_code'])
                else:
                    logger.info('Error updating {}'.format(yaml_versions))
                    raise

        # Update the local repository using prevously uploaded script.
        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            script_cmd = '{0}/{1}'.format(self.remote_path_scripts,
                                          self.ubuntu_script)
        else:
            script_cmd = '{0}/{1}'.format(self.remote_path_scripts,
                                          self.centos_script)
        script_result = remote.execute(script_cmd)
        assert_equal(0, script_result['exit_code'])

        self.env.make_snapshot("prepared_{}".format(self.ready_snapshot),
                               is_make=True)

    @test(depends_on=[prepare_repository],
          groups=["deploy_newpkgs_pr_ha"])
    @log_snapshot_on_error
    def deploy_newpkgs_pr_ha(self):
        """Deploy cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster network

        Snapshot: deploy_newpkgs_pr_ha

        """
        self.env.revert_snapshot("prepared_{}".format(self.ready_snapshot))

        settings_pr = None

        if settings.NEUTRON_ENABLE:
            settings_pr = {
                "net_provider": 'neutron',
                "net_segment_type": "gre"
            }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=settings_pr
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id, is_feature=True)

        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.env.verify_network_configuration("slave-01")
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster()
        )

        self.env.make_snapshot("deploy_newpkgs_pr_ha", is_make=True)
