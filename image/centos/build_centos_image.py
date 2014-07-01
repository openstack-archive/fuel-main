# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This script is partly based on https://github.com/katzj/ami-creator

import argparse
import logging
import os
import shutil
import sys
import tempfile

import imgcreate
from imgcreate.fs import BindChrootMount
from imgcreate.kickstart import FirewallConfig
# this monkey patch is for avoiding anaconda bug with firewall configuring
FirewallConfig.apply = lambda x, y: None

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler(sys.stdout))


class ImageCreator(imgcreate.LoopImageCreator):
    MODULES = [
        'xenblk',
        'xen_blkfront',
        'virtio_net',
        'virtio_pci',
        'virtio_blk',
        'virtio_balloon',
        'e1000',
        'sym53c8xx',
        'scsi_transport_sas',
        'mptbase',
        'mptscsih',
        'sd_mod',
        'mptsas',
        'sg'
    ]

    def __init__(self, ksfile, name, tmpdir=None,
                 cachedir=None, export_kernel=False):
        super(ImageCreator, self).__init__(
            imgcreate.read_kickstart(ksfile), name, '/')
        self.tmpdir = tmpdir or tempfile.gettempdir()
        if not os.path.exists(self.tmpdir):
            LOG.info('Creating tmp directory')
            os.makedirs(self.tmpdir)
        self.cachedir = cachedir or os.path.join(os.getcwd(), 'cache')
        self.export_kernel = export_kernel
        self.MODULES.extend(imgcreate.kickstart.get_modules(self.ks))

        # this will mount mirror into chroot and then unmount
        self.__ensure_builddir()
        self.__bindmounts = [BindChrootMount('/mirror', self._instroot)]

    def _get_fstab(self):
        s = 'LABEL=_/ / %s defaults 0 0\n' % self._fstype
        s += self._get_fstab_special()
        return s

    def _get_kernel_options(self):
        s = imgcreate.kickstart.get_kernel_args(self.ks, default = 'ro')
        return s

    def _create_bootconfig(self):
        LOG.info('Preparing bootloader config')
        imgtemplate = """
title %(title)s %(version)s
        root (hd0)
        kernel /boot/%(kernel)s root=LABEL=_/ %(bootargs)s
        initrd /boot/%(initrd)s

"""
        cfg = """
default=0
timeout=%(timeout)s
""" % {'timeout': imgcreate.kickstart.get_timeout(self.ks, 5)}

        kernels = self._get_kernel_versions()
        for version in reduce(lambda x, y: x + y, kernels.values(), []):
            kernel = 'vmlinuz-%s' % version
            initrd = 'initrd-%s.img' % version
            if not os.path.exists(self._instroot + '/boot/' + initrd):
                initrd = 'initramfs-%s.img' % version

            cfg += imgtemplate % {
                'title': self.name, 'initrd': initrd, 'kernel': kernel,
                'version': version, 'bootargs': self._get_kernel_options()}

        with open(self._instroot + '/boot/grub/grub.conf', 'w') as f:
            f.write(cfg)

    def _custom_export_kernel(self):
        LOG.info('Extracting kernel and initramfs')
        for filename in os.listdir(self._instroot + '/boot'):
            if filename.startswith('initr') or filename.startswith('vmlinuz'):
                shutil.copyfile(self._instroot + '/boot/' + filename,
                                os.path.join(os.getcwd(),filename))

    def _custom_dracut_conf(self):
        LOG.info('Preparing dracut configuration')
        filename = os.path.join(self._instroot, '/etc/dracut.conf.d/fuel.conf')
        directory = os.path.dirname(filename)
        os.path.exists(directory) or os.makedirs(directory)
        config = """
filesystems+=' %(image_filesystem)s '
drivers+=' %(modules)s '
""" % {'image_filesystem': self._fstype,
       'modules': ' '.join(self.MODULES)}
        with open(filename, 'w') as f:
            f.write(config)

    def create(self):
        self.mount(cachedir=self.cachedir)
        self._custom_dracut_conf()
        self.install()
        self.configure()
        if self.export_kernel:
            self._custom_export_kernel()
        self.unmount()
        self.package()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-k', '--kickstart', dest='kickstart', action='store', type=str,
        help='kickstart file', required=True
    )
    parser.add_argument(
        '-n', '--name', dest='name', action='store', type=str,
        help='image name', required=True
    )
    parser.add_argument(
        '-c', '--cache', dest='cache', action='store', type=str,
        help='cache directory'
    )
    parser.add_argument(
        '-t', '--tmp', dest='tmp', action='store', type=str,
        help='tmp directory'
    )
    parser.add_argument(
        '-e', '--export', dest='export', action='store_true',
        help='export kernel and miniroot out of image', default=True
    )
    return parser


def main():
    parser = parse_args()
    params, other_params = parser.parse_known_args()

    creator = ImageCreator(
        params.kickstart, params.name,
        tmpdir=params.tmp, cachedir=params.cache, export_kernel=params.export)

    try:
        creator.create()
    except imgcreate.CreatorError, e:
        LOG.error('Error: %s' %(e,))
        return 1
    finally:
        creator.cleanup()
    return 0


if __name__ == '__main__':
    main()
