import os
import re

BROWSER = os.environ.get('BROWSER', 'firefox')

# download it here http://chromedriver.storage.googleapis.com/index.html
CHROME_EXECUTABLE_PATH = \
    os.environ.get('CHROME_EXECUTABLE_PATH', '/usr/bin/google-chrome')

NAILGUN_FOLDER = os.environ.get('NAILGUN_FOLDER')

FOLDER_SCREEN_EXPECTED = os.environ.get(
    'FOLDER_SCREEN_EXPECTED', '/home/nfedotov/testscreens/expected')
FOLDER_SCREEN_CURRENT = os.environ.get(
    'FOLDER_SCREEN_CURRENT', '/home/nfedotov/testscreens/current')

OPENSTACK_RELEASE_CENTOS = os.environ.get(
    'OPENSTACK_RELEASE_CENTOS', 'Havana on CentOS 6.4 (2013.2.2)')
OPENSTACK_RELEASE_REDHAT = os.environ.get(
    'OPENSTACK_RELEASE_REDHAT', 'RHOS 3.0 for RHEL 6.4 (2013.2.2)')
OPENSTACK_RELEASE_UBUNTU = os.environ.get(
    'OPENSTACK_RELEASE_UBUNTU', 'Havana on Ubuntu 12.04 (2013.2.2)')

REDHAT_USERNAME = os.environ.get('REDHAT_USERNAME', 'rheltest')
REDHAT_PASSWORD = os.environ.get('REDHAT_PASSWORD', 'password')
REDHAT_SATELLITE = os.environ.get('REDHAT_SATELLITE', 'satellite.example.com')
REDHAT_ACTIVATION_KEY = os.environ.get(
    'REDHAT_ACTIVATION_KEY', '1234567890')

openstack_name = lambda release: re.sub('\s\\(.*?\\)$', '', release)
OPENSTACK_CENTOS = openstack_name(OPENSTACK_RELEASE_CENTOS)
OPENSTACK_REDHAT = openstack_name(OPENSTACK_RELEASE_REDHAT)
OPENSTACK_UBUNTU = openstack_name(OPENSTACK_RELEASE_UBUNTU)

NAILGUN_FIXTURES = os.environ.get('NAILGUN_FIXTURES', '')

URL_HOME = os.environ.get('URL_HOME', 'http://localhost:8000/')

SELENIUM_IMPLICIT_WAIT = os.environ.get('SELENIUM_IMPLICIT_WAIT', 10)
