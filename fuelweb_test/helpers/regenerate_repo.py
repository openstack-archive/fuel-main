#    Copyright 2014 Mirantis, Inc.
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


from proboscis.asserts import assert_equal
from xml.etree import ElementTree

from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test import logger
from fuelweb_test import settings

import traceback
import re
import urllib2
import zlib


class CustomRepo(object):

    def __init__(self):
        self.env = EnvironmentModel()
        self.path_scripts = './fuelweb_test/helpers/'
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
        self.pkgs_list = []

        self.custom_pkgs_mirror_path = ''
        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            # Trying to determine the root of Ubuntu repository
            pkgs_path = settings.CUSTOM_PKGS_MIRROR.split('/dists/')
            if len(pkgs_path) == 2:
                self.custom_pkgs_mirror = pkgs_path[0]
                self.custom_pkgs_mirror_path = '/dists/{}'.format(pkgs_path[1])
            else:
                self.custom_pkgs_mirror = settings.CUSTOM_PKGS_MIRROR
        else:
            self.custom_pkgs_mirror = settings.CUSTOM_PKGS_MIRROR

    def prepare_repository(self):
        """Prepare admin node to packages testing

        Scenario:
            1. Temporary set nameserver to local router on admin node
            2. Install tools to manage rpm/deb repository
            3. Retrive list of packages from custom repository
            4. Download packages to local rpm/deb repository
            5. Update .yaml file with new packages version
            6. Re-generate repo using shell scripts on admin node

        """
        # Check necessary settings and revert a snapshot
        if not self.custom_pkgs_mirror:
            return
        logger.info("Custom mirror with new packages: {0}"
                    .format(settings.CUSTOM_PKGS_MIRROR))

        # Modify admin resolv.conf to use local host resolver
        dns_server = self.env.router()
        new_resolv_conf = ["nameserver {0}".format(dns_server)]
        old_resolv_conf = self.modify_resolv_conf(new_resolv_conf)

        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            # Ubuntu
            master_tools = ['dpkg', 'dpkg-devel']
            self.install_tools(master_tools)
            self.get_pkgs_list_ubuntu()
            pkgs_local_path = '{0}/pool/main/'\
                              .format(self.local_mirror_ubuintu)
            self.download_pkgs(pkgs_local_path)
            self.update_yaml(self.ubuntu_yaml_versions)
            self.regenerate_repo(self.ubuntu_script)
        else:
            # CentOS
            master_tools = ['createrepo']
            self.install_tools(master_tools)
            self.get_pkgs_list_centos()
            pkgs_local_path = '{0}/Packages/'.format(self.local_mirror_centos)
            self.download_pkgs(pkgs_local_path)
            self.update_yaml(self.centos_yaml_versions)
            self.regenerate_repo(self.centos_script)

        # Restore original admin resolv.conf
        self.modify_resolv_conf(old_resolv_conf, merge=False)

    # Set the local router as nameserver that will allow
    # the admin node to access the Mirantis osci repositories.
    def modify_resolv_conf(self, nameservers=[], merge=True):
        remote = self.env.get_admin_remote()
        resolv_conf = remote.execute('cat /etc/resolv.conf')
        assert_equal(0, resolv_conf['exit_code'],
                     self.assert_msg('cat /etc/resolv.conf',
                                     resolv_conf['stderr']))
        if merge:
            nameservers.extend(resolv_conf['stdout'])
        resolv_new = "".join('{0}\n'.format(ns) for ns in nameservers
                             if 'nameserver' in ns)
        logger.debug('echo "{0}" > /etc/resolv.conf'
                     .format(resolv_new))
        echo_cmd = 'echo "{0}" > /etc/resolv.conf'.format(resolv_new)
        echo_result = remote.execute(echo_cmd)
        assert_equal(0, echo_result['exit_code'],
                     self.assert_msg(echo_cmd, echo_result['stderr']))
        return resolv_conf['stdout']

    # Install tools to masternode
    def install_tools(self, master_tools=[]):
        logger.info("Installing necessary tools for {0}"
                    .format(settings.OPENSTACK_RELEASE))
        for master_tool in master_tools:
            if (self.env.admin_install_pkg(master_tool)):
                logger.error('Cannot install package {0} on admin node.'
                             .format(master_tool))
                raise

    # Ubuntu: Creating list of packages from the additional mirror
    def get_pkgs_list_ubuntu(self):
        url = "{0}/{1}/Packages".format(self.custom_pkgs_mirror,
                                        self.custom_pkgs_mirror_path)
        logger.info("Retriving additional packages from the custom mirror:"
                    " {0}".format(url))
        try:
            pkgs_release = urllib2.urlopen(url).read()
        except (urllib2.HTTPError, urllib2.URLError):
            logger.error(traceback.format_exc())
            url_gz = '{0}.gz'.format(url)
            logger.info("Retriving additional packages from the custom mirror:"
                        " {0}".format(url_gz))
            try:
                pkgs_release_gz = urllib2.urlopen(url_gz).read()
            except (urllib2.HTTPError, urllib2.URLError):
                logger.error(traceback.format_exc())
                raise
            try:
                d = zlib.decompressobj(zlib.MAX_WBITS | 32)
                pkgs_release = d.decompress(pkgs_release_gz)
            except Exception:
                logger.error('Ubuntu mirror error: Could not decompress {0}\n'
                             '{1}'.format(url_gz, traceback.format_exc()))
                raise

        packages = (pkg for pkg in pkgs_release.split("\n\n") if pkg)
        for package in packages:
            upkg = {pstr.split()[0].lower(): ''.join(pstr.split()[1:])
                    for pstr in package.split("\n") if pstr[0].strip()}
            if (("package:" in upkg) and
                    ("version:" in upkg) and
                    ("filename:" in upkg)):
                # TODO: add dependences list to upkg
                self.pkgs_list.append(upkg)
            else:
                logger.error('Missing one of the statement "Package:", '
                             '"Version:" or "Filename:" in {0}'.format(url))
                raise

    # Centos: Creating list of packages from the additional mirror
    def get_pkgs_list_centos(self):
        logger.info("Retriving additional packages from the custom mirror: {0}"
                    .format(self.custom_pkgs_mirror))
        url = "{0}/repodata/repomd.xml".format(self.custom_pkgs_mirror)
        try:
            repomd_data = urllib2.urlopen(url).read()
        except (urllib2.HTTPError, urllib2.URLError):
            logger.error(traceback.format_exc())
            raise
        # Remove namespace attribute before parsing XML
        repomd_data = re.sub(' xmlns="[^"]+"', '', repomd_data, count=1)
        tree_repomd_data = ElementTree.fromstring(repomd_data)
        lists_location = ''
        for repomd in tree_repomd_data.findall('data'):
            if repomd.get('type') == 'primary':
                repomd_location = repomd.find('location')
                lists_location = repomd_location.get('href')
        if not lists_location:
            logger.error('CentOS mirror error: Could not parse {0}\n{1}'
                         .format(url, traceback.format_exc()))
            raise
        url = "{0}/{1}".format(self.custom_pkgs_mirror, lists_location)
        try:
            lists_data = urllib2.urlopen(url).read()
        except (urllib2.HTTPError, urllib2.URLError):
            logger.error(traceback.format_exc())
            raise
        if '.xml.gz' in lists_location:
            try:
                d = zlib.decompressobj(zlib.MAX_WBITS | 32)
                lists_data = d.decompress(lists_data)
            except Exception:
                logger.error('CentOS mirror error: Could not decompress {0}\n'
                             '{1}'.format(url, traceback.format_exc()))
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
                    # TODO: add dependences list to cpkg
                    self.pkgs_list.append(cpkg)

    # Download packages (local_folder)
    def download_pkgs(self, pkgs_local_path):
        # Process the packages list:
        total_pkgs = len(self.pkgs_list)
        logger.info('Found {0} custom package(s)'.format(total_pkgs))

        remote = self.env.get_admin_remote()
        for npkg, pkg in enumerate(self.pkgs_list):
            # TODO: Previous versions of the updating packages must be removed
            # to avoid unwanted packet manager dependences resolution
            # (when some package still depends on other package which
            # is not going to be installed)

            logger.info('({0}/{1}) Downloading package: {2}/{3}'
                        .format(npkg + 1, total_pkgs,
                                self.custom_pkgs_mirror,
                                pkg["filename:"]))
            wget_cmd = "wget --no-verbose --directory-prefix {0} {1}/{2}"\
                       .format(pkgs_local_path,
                               self.custom_pkgs_mirror,
                               pkg["filename:"])
            wget_result = remote.execute(wget_cmd)
            assert_equal(0, wget_result['exit_code'],
                         self.assert_msg(wget_cmd, wget_result['stderr']))

    # Update yaml (pacth_to_yaml)
    def update_yaml(self, yaml_versions):
            # Update the corresponding .yaml with the new package version.
        for pkg in self.pkgs_list:
            remote = self.env.get_admin_remote()
            result = remote.execute('grep -e "^{0}: " {1}'
                                    ''.format(pkg["package:"], yaml_versions))
            if result['exit_code'] == 0:
                sed_cmd = 'sed -i \'s/^{0}: .*/{0}: "{1}"/\' {2}'\
                          .format(pkg["package:"],
                                  pkg["version:"],
                                  yaml_versions)
                sed_result = remote.execute(sed_cmd)
                assert_equal(0, sed_result['exit_code'],
                             self.assert_msg(sed_cmd, sed_result['stderr']))
            else:
                if result['exit_code'] == 1:
                    echo_cmd = 'echo "{0}: \\"{1}\\"" >> {2}'\
                               .format(pkg["package:"],
                                       pkg["version:"],
                                       yaml_versions)
                    echo_result = remote.execute(echo_cmd)
                    assert_equal(0, echo_result['exit_code'],
                                 self.assert_msg(echo_cmd,
                                                 echo_result['stderr']))
                else:
                    logger.error('Error updating {0}\n{1}'
                                 .format(yaml_versions,
                                         traceback.format_exc()))
                    raise

    # Upload regenerate* script to masternode (script name)
    def regenerate_repo(self, regenerate_script):
        # Uploading scripts that prepare local repositories:
        # 'regenerate_centos_repo' and 'regenerate_ubuntu_repo'
        try:
            remote = self.env.get_admin_remote()
            remote.upload('{0}/{1}'.format(self.path_scripts,
                                           regenerate_script),
                          self.remote_path_scripts)
            remote.execute('chmod 755 {0}/{1}'.format(self.remote_path_scripts,
                                                      regenerate_script))
        except Exception:
            logger.error('Could not upload scripts for updating repositories.'
                         '\n{0}'.format(traceback.format_exc()))
            raise

        # Update the local repository using prevously uploaded script.
        script_cmd = '{0}/{1}'.format(self.remote_path_scripts,
                                      regenerate_script)
        script_result = remote.execute(script_cmd)
        assert_equal(0, script_result['exit_code'],
                     self.assert_msg(script_cmd, script_result['stderr']))

        logger.info('Local "{0}" repository has been updated successfuly.'
                    .format(settings.OPENSTACK_RELEASE))

    def assert_msg(self, cmd, err):
        return 'Executing \'{0}\' on the admin node has failed with: {1}'\
               .format(cmd, err)

    def check_puppet_logs(self):
        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            err_deps = self.check_puppet_logs_ubuntu()
        else:
            err_deps = self.check_puppet_logs_centos()

        for err_deps_key in err_deps:
            logger.info('Error: Package: {0} has unmet dependencies:'
                        .format(err_deps_key))
            for dep in err_deps[err_deps_key]:
                logger.info('        {0}'.format(dep.strip()))

    def check_puppet_logs_ubuntu(self):
        """ Checking puppet-agent.log files on all nodes for packets
            dependency errors during a cluster deploing (ubuntu)"""

        remote = self.env.get_admin_remote()

        err_start = 'The following packages have unmet dependencies:'
        err_end = 'Unable to correct problems,'\
                  ' you have held broken packages.'
        cmd = 'fgrep -h -e " Depends: " -e "{0}" -e "{1}" '\
              '/var/log/docker-logs/remote/node-*.test.domain.local/'\
              'puppet*.log'.format(err_start, err_end)
        result = remote.execute(cmd)['stdout']

        err_deps = {}
        err_deps_key = ''
        err_deps_flag = False

        # Forming a dictionary of package names
        # with sets of required packages.
        for res_str in result:
            if err_deps_flag:
                if err_end in res_str:
                    err_deps_flag = False
                elif len(res_str.split(": Depends:")) > 1:
                    split_deps_key = res_str.split(': Depends:')
                    err_deps_key = split_deps_key[0]
                    if err_deps_key not in err_deps:
                        err_deps[err_deps_key] = set()
                    if 'but it is not' in split_deps_key[1]:
                        err_deps[err_deps_key].add('Depends:{0}'
                                                   .format(split_deps_key[1]))
                elif 'Depends:' in res_str and err_deps_key:
                    if 'but it is not' in res_str:
                        err_deps[err_deps_key].add(res_str)
                else:
                    err_deps_key = ''
            elif err_start in res_str:
                err_deps_flag = True

        return err_deps

    def check_puppet_logs_centos(self):
        """ Checking puppet-agent.log files on all nodes for packets
            dependency errors during a cluster deploing (centos)"""

        remote = self.env.get_admin_remote()

        cmd = 'fgrep -h -e "Error: Package: " -e " Requires: " /var/log/'\
              'docker-logs/remote/node-*.test.domain.local/puppet*.log'
        result = remote.execute(cmd)['stdout']

        err_deps = {}
        err_deps_key = ''

        # Forming a dictionary of package names
        # with sets of required packages.
        for res_str in result:
            if 'Error: Package:' in res_str:
                if len(res_str.split('Error: Package: ')) > 1:
                    err_deps_key = res_str.split('Error: Package: ')[1]
                    if err_deps_key not in err_deps:
                        err_deps[err_deps_key] = set()
                else:
                    err_deps_key = ''
            elif ' Requires: ' in res_str and err_deps_key:
                err_deps[err_deps_key].add(res_str)
            else:
                err_deps_key = ''

        return err_deps
