#!/usr/bin/env python

import csv
import codecs
import cStringIO
import re
import sys
from launchpadlib.launchpad import Launchpad

PROJECT = 'fuel'
CURRENT_MILESTONE = '5.1'
teams = {
    'python': [
        'fuel-python', 'alekseyk-ru', 'dshulyak', 'rustyrobot', 'ikalnitsky',
        'nmarkov', 'aroma-x', 'akislitsky', 'kozhukalov', 'lux-place'
    ],
    'ui': [
        'fuel-ui', 'vkramskikh', 'astepanchuk', 'bdudko', 'kpimenova',
        'jkirnosova'
    ],
    'library': [
        'fuel-library', 'sgolovatiuk', 'xenolog', 'adidenko',
        'raytrac3r', 'idv1985', 'bogdando', 'vkuklin', 'sbogatkin',
    ],
    'l2': ['manashkin', 'ekozhemyakin'],
    'astute': ['fuel-astute', 'vsharshov'],
    'osci': [
        'fuel-osci', 'sotpuschennikov', 'dburmistrov', 'vparakhin', 'r0mikiam',
        'mrasskazov',
    ],
    'qa': [
        'fuel-qa', 'apalkina', 'aurlapova', 'tatyana-leontovich',
        'asledzinskiy', 'apanchenko-8', 'ykotko',
    ],
    'devops': ['fuel-devops', 'afedorova', 'teran', 'acharykov'],
    'us': ['dborodaenko', 'rmoe', 'xarses', 'dreidellhasa'],
    'mos': [
        'mos-linux', 'mos-neutron', 'mos-nova', 'mos-horizon',
        'mos-ceilometer', 'mos-oslo', 'mos-sahara',
    ],
    'partners': ['izinovik'],
}

lp = Launchpad.login_anonymously('fuel-bot', 'production', version='devel')
project = lp.projects[PROJECT]
blueprint_series = {}


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

csvfile = open('report.csv', 'wb')
reporter = UnicodeWriter(csvfile)
reporter.writerow([
    '', 'Link', 'Title', 'Status', 'Priority', 'Team', 'Nick', 'Name', 'Triage actions'
])

def printn(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def check_bp(bp):
    issues = []
    if bp.priority == 'Undefined':
        issues.append('No priority')
    if bp.priority == 'Not':
        issues.append('Not priority')
    if not bp.assignee:
        issues.append('No assignee')
    if not bp.milestone:
        issues.append('No milestone')
    if not bp.web_link in blueprint_series.keys():
        issues.append('No series')
    return issues


def check_bug(bug):
    issues = []
    if bug.importance == 'Undefined':
        issues.append('No priority')
    if not bug.assignee:
        issues.append('No assignee')
    if not bug.milestone:
        issues.append('No milestone')
    if bug.status == 'New':
        issues.append('Not triaged')
    if bug.milestone.name != CURRENT_MILESTONE:
        issues.append('Not related to current milestone')
    return issues

print("Collecting series:")

# Launchpad API does not allow to get series of a blueprint
for series in project.series:
    printn(" %s" % series.name)
    for bp in series.valid_specifications:
        blueprint_series[bp.web_link] = series.name

print  # /series

blueprints = project.valid_specifications
print("Processing blueprints (%d):" % len(blueprints))

for (counter, bp) in enumerate(blueprints, 1):
    if counter % 10 == 0:
        printn("%4d" % counter)
    if counter % 200 == 0:
        print
    assignee = 'unassigned'
    assignee_name = 'unassigned'
    try:
        assignee = bp.assignee.name
        assignee_name = bp.assignee.display_name
    except:
        pass
    team = 'unknown'
    status = 'error'
    for t in teams.keys():
        if assignee in teams[t]:
            team = t
    if bp.is_started and not bp.is_complete:
        status = 'in progress'
    if not bp.is_started and not bp.is_complete:
        status = 'backlog'
    if bp.is_complete:
        status = 'done'
    if status != 'done':
        reporter.writerow([
            'bp', bp.web_link, bp.title, bp.implementation_status, bp.priority,
            team, assignee, assignee_name, ', '.join(check_bp(bp))
        ])

print  # /blueprints

bugs = project.searchTasks()
print("Processing bugs (%d):" % len(bugs))

for (counter, bug) in enumerate(bugs, 1):
    if counter % 10 == 0:
        printn("%4d" % counter)
    if counter % 200 == 0:
        print
    assignee = 'unassigned'
    assignee_name = 'unassigned'
    try:
        assignee = bug.assignee.name
        assignee_name = bug.assignee.display_name
    except:
        pass
    team = 'unknown'
    status = 'backlog'
    for t in teams.keys():
        if assignee in teams[t]:
            team = t
    title = re.sub("^.*: \"(.*)\"$", '\\1', bug.title)
    if bug.is_complete:
        status = 'done'
    if bug.status == 'Fix Committed' or bug.status == 'Fix Released' \
            or bug.status == 'Incomplete':
        status = 'done'
    if bug.status == 'In Progress':
        status = 'in progress'
    if status != 'done':
        reporter.writerow([
            'bug', bug.web_link, title, bug.status, bug.importance, team,
            assignee, assignee_name, ', '.join(check_bug(bug))
        ])

print  # /bugs
