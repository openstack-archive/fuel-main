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
import os
#explicitly set editor for cmd2, will throw a lot of which /usr/bin/.. thrash
#this is known bug fixed in cmd2==0.6.6
os.environ['EDITOR'] = '/usr/bin/nano'
import sys
from cliff.app import App
from cliff.commandmanager import CommandManager
import logging


class DhcpApp(App):
    DEFAULT_VERBOSE_LEVEL = 0

    def __init__(self):
        super(DhcpApp, self).__init__(
            description='Dhcp check application',
            version='0.1',
            command_manager=CommandManager('dhcp.check'),
        )

    def configure_logging(self):
        super(DhcpApp, self).configure_logging()
        logger = logging.getLogger(None)
        logger.propagate = False
        runtime_logger = logging.getLogger('scapy.runtime')
        runtime_logger.setLevel(logging.ERROR)


def main(argv=sys.argv[1:]):
    myapp = DhcpApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
