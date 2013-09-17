#!/usr/bin/python
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

import setuptools


setuptools.setup(
    name="dhcp_checker",
    version='0.1',
    description="Utils for detecting dhcp servers and some other stuff",
    author="Dmitry Shulyak",
    author_email="yashulyak@gmail.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Security",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Software Development :: Testing"
    ],
    install_requires=[
        'cliff-tablib==1.1',
    ],
    include_package_data=True,
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'dhcpcheck = dhcp_checker.cli:main',
        ],
        'dhcp.check': [
            'discover = dhcp_checker.commands:ListDhcpServers',
            'request = dhcp_checker.commands:ListDhcpAssignment',
            'vlans = dhcp_checker.commands:DhcpWithVlansCheck'
        ],
    },
)
