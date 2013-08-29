#!/usr/bin/env python
import sys
import os

import argparse
import restkit
import re
import ConfigParser

import git_api


class Review(object):

    def __init__(self, params):
        self.git = git_api.GitEngine("local_repo", params.repo_url)
        self.github = None

        p = re.compile('git@github.com:(\S+)\/(\S+)\.git')
        self.user, self.repo = p.match(params.repo_url).groups()

        self.repo_url = params.repo_url
        self.remote_branch = params.remote_branch
        if params.origin_repo_url:
            self.origin_repo_url = params.origin_repo_url
        else:
            self.origin_repo_url = params.repo_url
        self.origin_branch = params.origin_branch
        self.origin_user, self.origin_repo = \
                p.match(self.origin_repo_url).groups()

        config = ConfigParser.ConfigParser()
        config.read(os.path.expanduser("~/.review.conf"))

        self.github_user = config.get('github', 'user')
        self.github_token = config.get('github', 'token')

    def rebase(self):
        self.git.fetch(refs_name='devel')
        self.git.fetch(remote_path=self.origin_repo_url, refs_name='origin')
        self.git.checkout_from_remote_branch("remotes/devel/%s" % \
                self.remote_branch)
        self.git.submodule_init()

        # Wipe all submodule's dirs before rebasing.
        self.git.wipe_all_submodules_helper()

        try:
            self.git.rebase("remotes/origin/%s" % self.origin_branch)
        except:
            raise Exception("ERROR: Auto-rebase of %s failed." \
                    " Try to 'git rebase origin/%s' from your local" \
                    "branch and push again" % \
                    (self.remote_branch, self.origin_branch))

        self.git.submodule_update()

    def push(self):
        self.git.push(remote_branch=self.origin_branch, \
                remote_path=self.origin_repo_url)
        # Remove remote branch as we don't need it after merge
        self.git.remove_remote_branch(remote_branch=self.remote_branch, \
                remote_path=self.repo_url)

        print "Closing pull request.."
        self._github_lazy_init()
        pull_requests = self.github.get_pull_request_by_label(self.origin_user,
                self.origin_repo, "%s:%s" % (self.user, self.remote_branch))

        if pull_requests:
            pull_number = pull_requests[0]['number']
            print "Found pull request #%s. Closing.." % pull_number
            newdata = {'state': 'closed'}
            self.github.update_pull_request(self.origin_user, self.origin_repo,
                    pull_number, newdata)

    def add_pull_request(self, title="default title", body="default body"):
        self._github_lazy_init()
        try:
            res = self.github.create_pull_request(self.user, self.repo,
                    self.origin_user, self.origin_branch,
                    self.remote_branch, title, body)
            pull_number = res['number']
        except restkit.errors.RequestFailed as e:
            print "Error occured while creating pull request." \
                    "Possibly it already exists."
            pull_requests = self.github.get_pull_request_by_label( \
                    self.origin_user, self.origin_repo, \
                    "%s:%s" % (self.user, self.remote_branch))
            pull_number = pull_requests[0]['number']
        url = "https://github.com/%s/%s/pull/%s" % \
                (self.origin_user, self.origin_repo, pull_number)
        print "<a href=\"%s\">Pull request #%s</a>" % \
                (url, pull_number)

    def _github_lazy_init(self):
        if not self.github:
            self.github = git_api.GithubEngine(self.github_user,
                    self.github_token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review system")
    parser.add_argument('--repo', dest='repo_url', type=str, required=True,
            help='URL to repository, format: git@github.com:<user>/<repo>.git')
    parser.add_argument('--branch', dest='remote_branch', type=str,
            required=True, help='Remote branch')
    parser.add_argument('--origin-repo', dest='origin_repo_url', type=str,
            required=False,
            help='URL to repository, format: git@github.com:<user>/<repo>.git')
    parser.add_argument('--origin-branch', dest='origin_branch',
            default='master', required=False, type=str,
            help='Remote branch')
    parser.add_argument('-t' '--pull_title', dest='pull_title', type=str,
            help='Title for pull request')
    parser.add_argument('-b' '--pull_body', dest='pull_body', type=str,
            help='Body for pull request')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--check', action='store_true',
            help='Check if branch can be rebased. Prepare it for tests.')
    group.add_argument('-a', '--add', action='store_true',
            help='Add pull request from user branch to master')
    group.add_argument('-p', '--push', action='store_true',
            help='Pushes rebased code from user branch to remote master')

    params = parser.parse_args()

    rvw = Review(params)

    # Expected flow:
    # 1. --check for attempts to rebase
    # 2. ./run_tests against current code (out of this script)
    # 3. --add  to create pull request on github
    # 4. Someone reviews code on github
    # 5. Release manager runs --push to rebase user branch and push to master

    if params.check:
        rvw.rebase()
    elif params.add:
        rvw.add_pull_request(params.pull_title, params.pull_body)
    elif params.push:
        rvw.rebase()
        rvw.push()

