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
import hashlib
import logging
import os
import shutil
import sys
import tempfile

import imgcreate
from imgcreate.errors import CreatorError
from imgcreate.errors import MountError
from imgcreate.fs import BindChrootMount
from imgcreate.fs import ExtDiskMount
from imgcreate.fs import makedirs
from imgcreate.fs import SparseLoopbackDisk
from imgcreate.kickstart import FirewallConfig
import yaml
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
                 cachedir=None, export_kernel=False,
                 separate_images=None, output_file=None):
        super(ImageCreator, self).__init__(
            imgcreate.read_kickstart(ksfile), name, '/')
        self.tmpdir = tmpdir or tempfile.gettempdir()
        if not os.path.exists(self.tmpdir):
            LOG.info('Creating tmp directory')
            os.makedirs(self.tmpdir)
        self.cachedir = cachedir or os.path.join(os.getcwd(), 'cache')
        self.export_kernel = export_kernel
        self.MODULES.extend(imgcreate.kickstart.get_modules(self.ks))

        self.__selinux_mountpoint = "/sys/fs/selinux"

        # this will mount mirror into chroot and then unmount
        self.__output_file = output_file
        self.__ensure_builddir()
        self.__bindmounts = [BindChrootMount('/mirror', self._instroot)]
        self.__separate_images = {}
        self.__separate_images_disks = []
        self.__imgdir = None
        for ent in separate_images.split():
            mountpoint, fs_type = ent.split(',')
            self.__separate_images[mountpoint] = fs_type

    def __get_image(self):
        if self.__imgdir is None:
            self.__imgdir = self._mkdtemp()
        return self.__imgdir + "/" + self.name + ".img"
    _image = property(__get_image)

    def _get_fstab(self):
        s = 'LABEL=_/ / %s defaults 0 0\n' % self._fstype
        s += self._get_fstab_special()
        return s

    def _get_kernel_options(self):
        s = imgcreate.kickstart.get_kernel_args(self.ks, default='ro')
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
                                os.path.join(os.getcwd(), filename))

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

    def _get_image_name(self, mountpoint):
        return self._mkdtemp() + "/" + self.name + \
            mountpoint.replace('/', '-') + ".img"

    def mount(self, base_on=None, cachedir=None):
        self.__ensure_builddir()
        makedirs(self._instroot)
        makedirs(self._outdir)
        self._mount_instroot(base_on)

        self.__fstype = self.__separate_images.pop('/')
        key = lambda x: len(x.rstrip('/').split('/'))
        for mountpoint in sorted(self.__separate_images.keys(), key=key):
            makedirs(self._instroot + mountpoint)
            loop_disk = ExtDiskMount(
                SparseLoopbackDisk(self._get_image_name(mountpoint),
                                   4 * 1024L * 1024 * 1024),
                self._instroot + mountpoint,
                self.__separate_images[mountpoint],
                4096,  # blocksize
                self.fslabel,
                self.tmpdir)
            self.__separate_images_disks.append(loop_disk)
            try:
                loop_disk.mount()
            except MountError, e:
                raise CreatorError("Failed to loopback mount '%s' : %s" %
                                   (self._get_image_name(mountpoint), e))
        self.__separate_images_disks.reverse()
        self.__separate_images_disks.append(self._LoopImageCreator__instloop)

        for d in ("/dev/pts", "/etc", "/boot", "/var/log", "/var/cache/yum",
                  "/sys", "/proc"):
            makedirs(self._instroot + d)

        cachesrc = cachedir or (self.__builddir + "/yum-cache")
        makedirs(cachesrc)
        # bind mount system directories into _instroot
        for (f, dest) in [("/sys", None), ("/proc", None),
                          ("/dev/pts", None), ("/dev/shm", None),
                          (self.__selinux_mountpoint,
                           self.__selinux_mountpoint),
                          (cachesrc, "/var/cache/yum")]:
            if os.path.exists(f):
                self.__bindmounts.append(BindChrootMount(f, self._instroot,
                                                         dest))
            else:
                logging.warn("Skipping (%s,%s) because source doesn't exist." %
                             (f, dest))

        self._do_bindmounts()
        self.__create_selinuxfs()
        self.__create_minimal_dev()
        os.symlink("/proc/self/mounts", self._instroot + "/etc/mtab")
        self.__write_fstab()

    def _yaml_data(self):
        def md5sum(filename, blocksize=1024 * 1024):
            hash = hashlib.md5()
            with open(filename, "rb") as f:
                for block in iter(lambda: f.read(blocksize), ""):
                    hash.update(block)
            return hash.hexdigest()

        data = {'repos': None, 'packages': None}
        for disk in self.__separate_images_disks:
            filename = os.path.basename(disk.disk.lofile)
            abs_path = os.path.join('/', os.path.basename(disk.disk.lofile))
            size = os.path.getsize(abs_path)
            md5 = md5sum(abs_path)
            mountpoint = filename[len(self.name):-4].replace('-', '/')
            if not mountpoint:
                mountpoint = '/'

            data.setdefault('images', []).append({
                'raw_md5': md5,
                'raw_size': size,
                'raw_name': None,
                'container_name': filename + '.gz',
                'container_md5': None,
                'container_size': None,
                'container': 'gzip',
                'format': disk.fstype})
        with open(self.__output_file, 'wb') as f:
            f.write(yaml.dump(data))

    def _stage_final_image(self):
        for disk in self.__separate_images_disks:
            disk.cleanup()
            minsize = disk._ExtDiskMount__resize_to_minimal()
            disk.disk.truncate(minsize)
            shutil.move(disk.disk.lofile, self._outdir + "/" +
                        os.path.basename(disk.disk.lofile))

    def unmount(self):
        self.__destroy_selinuxfs()
        self._undo_bindmounts()
        for disk in self.__separate_images_disks:
            disk.cleanup()

    def create(self):
        self.mount(cachedir=self.cachedir)
        self._custom_dracut_conf()
        self.install()
        self.configure()
        if self.export_kernel:
            self._custom_export_kernel()
        self.unmount()
        self.package()
        self._yaml_data()


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
    parser.add_argument(
        '-s', '--separate-images', dest='separate_images', action='store',
        type=str, help='separate images string', default='/boot,ext2 /,ext4'
    )
    parser.add_argument(
        '-O', '--output-file', dest='output_file', action='store',
        type=str, required=False, default="profile.yaml",
        help='Yaml file to store image metadata',
    )
    return parser


def main():
    parser = parse_args()
    params, other_params = parser.parse_known_args()

    creator = ImageCreator(
        params.kickstart, params.name,
        tmpdir=params.tmp, cachedir=params.cache, export_kernel=params.export,
        separate_images=params.separate_images, output_file=params.output_file)

    try:
        creator.create()
    except imgcreate.CreatorError, e:
        LOG.error('Error: %s' % (e,))
        return 1
    finally:
        creator.cleanup()
    return 0


if __name__ == '__main__':
    main()
