#!/usr/bin/python -tt
#
# ami-creator: Create an EC2 AMI image
#
# Copyright 2010, Jeremy Katz
# Jeremy Katz <katzj@fedoraproject.org>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import logging
import optparse
import os
import sys
import shutil

import imgcreate
from imgcreate.kickstart import FirewallConfig
# this monkey patch is for avoiding anaconda bug with firewall configuring
FirewallConfig.apply = lambda x, y: None

import rpmUtils.arch

class Usage(Exception):
    def __init__(self, msg = None):
        Exception.__init__(self, msg)

def parse_options(args):
    parser = optparse.OptionParser()

    # options related to the image
    imgopt = optparse.OptionGroup(parser, "Image options",
                                  "These options define the created image.")
    imgopt.add_option("-c", "--config", type="string", dest="kscfg",
                      help="Path or url to kickstart config file")
    imgopt.add_option("-n", "--name", type="string", dest="name",
                      help="Name to use for the image")
    imgopt.add_option("-e", "--extract-bootfiles", action="store_true", dest="extract_bootfiles",
                      help="Extract the kernel and ramdisk from the image")
    parser.add_option_group(imgopt)

    # options related to the config of your system
    sysopt = optparse.OptionGroup(parser, "System directory options",
                                  "These options define directories used on your system for creating the ami")
    sysopt.add_option("-t", "--tmpdir", type="string",
                      dest="tmpdir", default="/var/tmp",
                      help="Temporary directory to use (default: /var/tmp)")
    sysopt.add_option("", "--cache", type="string",
                      dest="cachedir", default=None,
                      help="Cache directory to use (default: private cache")
    parser.add_option_group(sysopt)

    imgcreate.setup_logging(parser)

    # debug options not recommended for "production" images
    # Start a shell in the chroot for post-configuration.
    parser.add_option("-l", "--shell", action="store_true", dest="give_shell",
                      help=optparse.SUPPRESS_HELP)


    (options, args) = parser.parse_args()
    if not options.kscfg:
        raise Usage("Kickstart file must be provided")

    return options

class AmiCreator(imgcreate.LoopImageCreator):
    def __init__(self, *args, **kwargs):
        imgcreate.LoopImageCreator.__init__(self, *args, **kwargs)

        # amis need xenblk at least
        self.__modules = ["xenblk", "xen_blkfront", "virtio_net", "virtio_pci",
                          "virtio_blk", "virtio_balloon", "e1000", "sym53c8xx",
                          "scsi_transport_sas", "mptbase", "mptscsih",
                          "sd_mod", "mptsas", "sg" ]
        self.__modules.extend(imgcreate.kickstart.get_modules(self.ks))

    # FIXME: refactor into imgcreate.LoopImageCreator
    def _get_kernel_options(self):
        """Return a kernel options string for bootloader configuration."""
        r = imgcreate.kickstart.get_kernel_args(self.ks, default = "ro")
        return r

    def _get_fstab(self):
        s = "LABEL=_/   /        %s      defaults         0 0\n" % self._fstype

        s += self._get_fstab_special()
        return s

    def _create_bootconfig(self):
        imgtemplate = """title %(title)s %(version)s
        root (hd0)
        kernel /boot/vmlinuz-%(version)s root=LABEL=_/ %(bootargs)s
        initrd /boot/%(initrdfn)s-%(version)s.img
"""

        cfg = """default=0
timeout=%(timeout)s

""" % { "timeout": imgcreate.kickstart.get_timeout(self.ks, 5) }

        kernels = self._get_kernel_versions()
        versions = []
        for ktype in kernels:
            versions.extend(kernels[ktype])

        for version in versions:
            if os.path.exists(self._instroot + "/boot/initrd-%s.img" %(version,)):
                initrdfn = "initrd"
            else:
                initrdfn = "initramfs"

            cfg += imgtemplate % {"title": self.name,
                                  "version": version,
                                  "initrdfn": initrdfn,
                                  "bootargs": self._get_kernel_options()}

        with open(self._instroot + "/boot/grub/grub.conf", "w") as grubcfg:
            grubcfg.write(cfg)

        # ec2 (pvgrub) expects to see /boot/grub/menu.lst
        os.link(self._instroot + "/boot/grub/grub.conf",
                self._instroot + "/boot/grub/menu.lst")

    def extract_bootfiles(self):
        for x in os.listdir(self._instroot + "/boot"):
            if not (x.startswith("initr") or x.startswith("vmlinuz")):
                continue
            logging.info("Extracting " + x)
            shutil.copyfile(self._instroot + "/boot/" + x, x)

    def __write_dracut_conf(self, cfgfn):
        if not os.path.exists(os.path.dirname(cfgfn)):
            os.makedirs(os.path.dirname(cfgfn))

        cfg = """
filesystems+="%(rootfs)s"
drivers+="%(modules)s"
""" % {"rootfs": self._fstype,
       "modules": " ".join(self.__modules)}

        with open(cfgfn, "w") as f:
            f.write(cfg)

    def __write_mkinitrd_conf(self, cfgfn):
        if not os.path.exists(os.path.dirname(cfgfn)):
            os.makedirs(os.path.dirname(cfgfn))

        cfg = """
PROBE="no"
MODULES+="%(rootfs)s "
MODULES+="%(modules)s "
rootfs="%(rootfs)s"
rootopts="defaults"
""" % {"rootfs": self._fstype,
       "modules": " ".join(self.__modules)}

        with open(cfgfn, "w") as f:
            f.write(cfg)
        os.chmod(cfgfn, 0755)

    def _mount_instroot(self, base_on = None):
        imgcreate.LoopImageCreator._mount_instroot(self, base_on)
        # we only support rhel/centos5 for mkinitrd because of
        # config incompatibilities.  blargh.
        self.__write_mkinitrd_conf(self._instroot + "/etc/sysconfig/mkinitrd/ami.conf")
        # and rhel/centos6 and current fedora (f12+) use dracut anyway
        self.__write_dracut_conf(self._instroot + "/etc/dracut.conf.d/ami.conf")

    def package(self, destdir="."):
        imgcreate.LoopImageCreator.package(self, destdir)


def main():
    try:
        options = parse_options(sys.argv[1:])
    except Usage, msg:
        logging.error(msg)
        return 1

    if os.geteuid() != 0:
        logging.error("ami-creator must be run as root")
        return 1

    ks = imgcreate.read_kickstart(options.kscfg)
    name = imgcreate.build_name(options.kscfg)
    if options.name:
        name = options.name

    creator = AmiCreator(ks, name, "/")
    creator.tmpdir = os.path.abspath(options.tmpdir)
    if options.cachedir:
        options.cachedir = os.path.abspath(options.cachedir)

    try:
        creator.mount(cachedir=options.cachedir)
        creator.install()
        creator.configure()
        if options.extract_bootfiles:
            creator.extract_bootfiles()
        if options.give_shell:
            print "Launching shell. Exit to continue."
            print "----------------------------------"
            creator.launch_shell()
        creator.unmount()
        creator.package()
    except imgcreate.CreatorError, e:
        logging.error("Error creating ami: %s" %(e,))
        return 1
    finally:
        creator.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())
