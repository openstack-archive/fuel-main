import os
import os.path
import pprint

from setuptools import setup
from setuptools import find_packages


# here = os.path.abspath(os.path.dirname(__file__))
# README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'SQLAlchemy==0.7.9',
    'web.py==0.37',
    'uWSGI==1.3',
    'greenlet==0.4.0',
    'eventlet==0.9.17',
    'kombu==2.4.7',
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
          scripts=['manage.py'],
          entry_points={
              'console_scripts': [
                  'nailgun_syncdb = nailgun.db:syncdb',
              ],
          },
          data_files=recursive_data_files([('usr/share/nailgun', 'static')])
          )
