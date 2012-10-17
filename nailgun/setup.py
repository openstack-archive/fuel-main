import os
import os.path
import pprint

from setuptools import setup
from setuptools import find_packages


# here = os.path.abspath(os.path.dirname(__file__))
# README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'SQLAlchemy',
    'web.py',
    'uWSGI',
    'greenlet',
    'eventlet',
    'kombu',
    # 'cobbler',
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
          entry_points={
              'console_scripts': [
                  'nailgun_syncdb = nailgun.db:syncdb',
              ],
          },
          data_files=recursive_data_files([('usr/share/nailgun', 'static')])
          )
