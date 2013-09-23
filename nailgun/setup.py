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
    'Jinja2==2.7',
    'Paste==1.7.5.1',
    'PyYAML==3.10',
    'SQLAlchemy==0.7.8',
    'amqplib==1.0.2',
    'anyjson==0.3.1',
    'argparse==1.2.1',
    'decorator==3.4.0',
    'kombu==2.1.8',
    'netaddr==0.7.10',
    'nose2==0.4.1',
    'nose==1.1.2',
    'pycrypto==2.6',
    'simplejson==2.6.2',
    'web.py==0.37',
    'wsgilog==0.3',
    'wsgiref==0.1.2',
    'fysom==1.0.11',
    'jsonschema==2.0.0',
]

major_version = '0.1'
minor_version = '0'
name = 'Nailgun'

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
          description='Nailgun package',
          long_description="""Nailgun package""",
          classifiers=[
              "Development Status :: 4 - Beta",
              "Programming Language :: Python",
              "Topic :: Internet :: WWW/HTTP",
              "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          ],
          author='Mirantis Inc.',
          author_email='product@mirantis.com',
          url='http://mirantis.com',
          keywords='web wsgi nailgun mirantis',
          packages=find_packages(),
          zip_safe=False,
          install_requires=requires,
          include_package_data=True,
          scripts=['manage.py'],
          entry_points={
              'console_scripts': [
                  'nailgun_syncdb = nailgun.db:syncdb',
                  'nailgun_fixtures = \
                      nailgun.fixtures.fixman:upload_fixtures',
                  'nailgund = nailgun.wsgi:appstart',
              ],
          },
          data_files=recursive_data_files([('share/nailgun', 'static')])
          )
