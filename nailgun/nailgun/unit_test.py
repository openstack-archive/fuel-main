# -*- coding: utf-8 -*-

import nose
import nose.config
from nose.plugins.xunit import Xunit
from nose.plugins.manager import PluginManager

import nailgun.test as test


class TestRunner(object):

    @classmethod
    def run(cls, *args, **kwargs):
        nc = nose.config.Config()
        nc.verbosity = 3
        nc.plugins = PluginManager(plugins=[Xunit()])
        nose.main(module=test, config=nc, argv=[
            __file__,
            "--with-xunit",
            "--xunit-file=nosetests.xml"
        ])
