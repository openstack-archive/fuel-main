from distutils.core import setup

setup(
    name='devops',
    version='0.1',
    description='Library to aid creating and manipulating virtual environments',
    author='Mirantis, Inc.',
    author_email='product@mirantis.com',
    packages=['devops', 'devops.driver'],
    scripts=['bin/devops'], requires=['xmlbuilder', "ipaddr", "paramiko"]
)

