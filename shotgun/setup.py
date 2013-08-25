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


import os
import os.path
import pprint

from setuptools import setup
from setuptools import find_packages


requires = [
    'Fabric==1.7.0'
]

major_version = '0.1'
minor_version = '0'
name = 'Shotgun'

version = "%s.%s" % (major_version, minor_version)


def recursive_data_files(spec_data_files):
    result = []
    for dstdir, srcdir in spec_data_files:
        for topdir, dirs, files in os.walk(srcdir):
            for f in files:
                result.append((os.path.join(dstdir, topdir),
                               [os.path.join(topdir, f)]))
    return result


if __name__ == "__main__":
    setup(name=name,
          version=version,
          description='Shotgun package',
          long_description="""Shotgun package""",
          classifiers=[
              "Development Status :: 4 - Beta",
              "Programming Language :: Python",
          ],
          author='Mirantis Inc.',
          author_email='product@mirantis.com',
          url='http://mirantis.com',
          keywords='shotgun mirantis',
          packages=find_packages(),
          zip_safe=False,
          install_requires=requires,
          include_package_data=True,
    )
