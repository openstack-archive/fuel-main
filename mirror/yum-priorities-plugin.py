#!/usr/bin/python
#
# yum-plugin-priorities 0.0.7
#
# Copyright (c) 2006-2007 Daniel de Kok
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# This plugins is inspired by the protectbase plugin, and enables/disables
# packages based on a repository priority.
#
# You can install this plugin by copying it to /usr/lib/yum-plugins. To
# enable this plugin, make sure that you have 'plugins=1' in /etc/yum.conf,
# and create the file /etc/yum/pluginconf.d/priorities.conf with the
# following content:
#
# [main]
# enabled=1
#
# If you also want the plugin to protect high-priority repositories against
# obsoletes in low-priority repositories, enable the 'check_obsoletes' bool:
#
# check_obsoletes=1
#
# By default, this plugin excludes packages from lower priority repositories
# based on the package name. If you want to exclude packages based ony the
# package name and architecture, enable the 'only_samearch' bool:
#
# only_samearch=N
#
# You can add priorities to repositories, by adding the line:
#
# priority=N
#
# to the repository entry, where N is an integer number. The default
# priority for repositories is 99. The repositories with the lowest
# number have the highest priority.
#
# Please report errors to Daniel de Kok <danieldk@pobox.com>

from yum.constants import *
from yum.plugins import TYPE_CORE
from yum import config
import yum

check_obsoletes = False
only_samearch = False

requires_api_version = '2.1'
plugin_type = (TYPE_CORE,)

def config_hook(conduit):
    global check_obsoletes
    global only_samearch

    # Plugin configuration
    check_obsoletes = conduit.confBool('main', 'check_obsoletes', default = False)
    only_samearch = conduit.confBool('main', 'only_samearch', default = False)

    # Repo priorities
    if yum.__version__ >= '2.5.0':
        # New style : yum >= 2.5
        config.RepoConf.priority = config.IntOption(99)
    else:
        # Old add extra options style
        conduit.registerOpt('priority', PLUG_OPT_INT, PLUG_OPT_WHERE_REPO, 99)

    # Command-line options.
    parser = conduit.getOptParser()
    if parser:
        if hasattr(parser, 'plugin_option_group'):
            parser = parser.plugin_option_group
        parser.add_option('', '--samearch-priorities', dest='samearch',
            action='store_true', default = False,
            help="Priority-exclude packages based on name + arch")

def _all_repo_priorities_same(allrepos):
    """ Are all repos are at the same priority """
    first = None
    for repo in allrepos:
        if first is None:
            first = repo.priority
        elif first != repo.priority:
            return False
    return True

def exclude_hook(conduit):
    global only_samearch
    global check_obsoletes

    allrepos = conduit.getRepos().listEnabled()

    # If they haven't done anything, don't do any work
    if _all_repo_priorities_same(allrepos):
        return
    
    # Check whether the user specified the --samearch option.
    opts, commands = conduit.getCmdLine()
    if opts and opts.samearch:
        only_samearch = True

    cnt = 0
    if check_obsoletes and not conduit._base.conf.obsoletes:
        check_obsoletes = False
    if check_obsoletes:
        obsoletes = conduit._base.up.rawobsoletes

    # Build a dictionary with package priorities. Either with arch or
    # archless, based on the user's settings.
    if only_samearch:
        pkg_priorities = dict()
    if check_obsoletes or not only_samearch:
        pkg_priorities_archless = dict() 
    for repo in allrepos:
        if repo.enabled:
            if only_samearch:
                repopkgs = _pkglist_to_dict(conduit.getPackages(repo), repo.priority, True)
                _mergeprioritydicts(pkg_priorities, repopkgs)

            if check_obsoletes or not only_samearch:
                repopkgs_archless = _pkglist_to_dict(conduit.getPackages(repo), repo.priority)
                _mergeprioritydicts(pkg_priorities_archless, repopkgs_archless)

    # Eliminate packages that have a low priority
    for repo in allrepos:
        if repo.enabled:
            for po in conduit.getPackages(repo):
                delPackage = False

                if only_samearch:
                    key = "%s.%s" % (po.name,po.arch)
                    if key in pkg_priorities and pkg_priorities[key] < repo.priority:
                        delPackage = True
                else:
                    key = "%s" % po.name
                    if key in pkg_priorities_archless and pkg_priorities_archless[key] < repo.priority:
                        delPackage = True

                if delPackage:
                    conduit.delPackage(po)
                    cnt += 1
                    conduit.info(3," --> %s from %s excluded (priority)" % (po,po.repoid))

                # If this packages obsoletes other packages, check whether
                # one of the obsoleted packages is not available through
                # a repo with a higher priority. If so, remove this package.
                if check_obsoletes:
                    if po.pkgtup in obsoletes:
                        obsolete_pkgs = obsoletes[po.pkgtup]
                        for obsolete_pkg in obsolete_pkgs:
                            pkg_name = obsolete_pkg[0]
                            if pkg_name in pkg_priorities_archless and pkg_priorities_archless[pkg_name] < repo.priority:
                                conduit.delPackage(po)
                                cnt += 1
                                conduit.info(3," --> %s from %s excluded (priority)" % (po,po.repoid))
                                break
    if cnt:
        conduit.info(2, '%d packages excluded due to repository priority protections' % cnt)
    if check_obsoletes:
        #  Atm. the update object doesn't get updated when we manually exclude
        # things ... so delete it. This needs to be re-written.
        conduit._base.up = None

def _pkglist_to_dict(pl, priority, addArch = False):
    out = dict()
    for p in pl:
        if addArch:
            key = "%s.%s" % (p.name,p.arch)
            out[key] = priority
        else:
            out[p.name] = priority
    return out

def _mergeprioritydicts(dict1, dict2):
    for package in dict2.keys():
        if package not in dict1 or dict2[package] < dict1[package]:
            dict1[package] = dict2[package]
