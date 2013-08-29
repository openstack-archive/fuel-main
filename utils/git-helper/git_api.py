#!/usr/bin/env python

import subprocess
import sys
import os

import json
from restkit import Resource, BasicAuth, Connection, request
from socketpool import ConnectionPool


class GithubEngine(object):

    def __init__(self, user, token):
        self.pool = ConnectionPool(factory=Connection)
        self.token = token
        self.headers = {'Content-Type': 'application/json',
                'Authorization': 'token %s' % self.token}

    # We don't use this method, but it can be useful in some cases
    def create_token(self, user, password):
        serverurl = "https://api.github.com"
        auth = BasicAuth(user, password)
        authreqdata = {"scopes": ["repo"], "note": "admin script"}
        resource = Resource('https://api.github.com/authorizations',
                pool=self.pool, filters=[auth])
        response = resource.post(headers={"Content-Type": "application/json"},
                payload=json.dumps(authreqdata))
        self.token = json.loads(response.body_string())['token']

    def list_repos(self):
        resource = Resource('https://api.github.com/user/repos',
                pool=self.pool)
        response = resource.get(headers=self.headers)
        return json.loads(response.body_string())

    def get_pull_request_by_label(self, user, repo, label):
        resource = Resource("https://api.github.com/repos/%s/%s/pulls" %
                (user, repo))
        pulls = json.loads(resource.get(headers=self.headers).body_string())
        pulls_by_label = filter(lambda p: p['head']['label']==label, pulls)

        return pulls_by_label  # I hope there is no more than one

    def update_pull_request(self, user, repo, number, data):
        resource = Resource("https://api.github.com/repos/%s/%s/pulls/%s" %
                (user, repo, number))
        res = resource.post(headers=self.headers,
                payload=json.dumps(data))
        return json.loads(res.body_string())

    def create_pull_request(self, user, repo, to_user, base_branch,
                branch, title="", body=""):
        if not title:
            title = "Robot pull request. Please review."
        resource = Resource("https://api.github.com/repos/%s/%s/pulls" %
                (to_user, repo))
        pulldata = {
                "title": title, "body": body,
                "head": "%s:%s" % (user, branch),
                "base": base_branch
        }
        response = resource.post(headers=self.headers,
                payload=json.dumps(pulldata))
        return json.loads(response.body_string())


class GitEngine(object):

    def __init__(self, local_repo, repo_url):
        self.local_repo = local_repo
        self.remote_path = repo_url
        self.local_branch = "temp-for-engine"
        self.refs_name = "origin"
        try:
            # Raises exception if can't change dir or can't get git info
            self.__exec("git status")
        except:
            # Let's create repo dir and initialize repo.
            self.__exec("mkdir %s" % local_repo, ".")
        self.__exec("git init")

    def __exec(self, command, cwd=None):
        if not cwd:
            cwd = self.local_repo
        print "Executing command %s in cwd=%s" % (command, cwd)
        proc = subprocess.Popen(command, cwd=cwd, \
                     stderr=subprocess.PIPE, \
                     stdout=subprocess.PIPE, \
                     shell=True)
        try:
            stdout_value = proc.stdout.read().rstrip()
            stderr_value = proc.stderr.read().rstrip()
            status = proc.wait()
        finally:
            proc.stdout.close()
            proc.stderr.close()

        if status != 0:
            print "ERRROR: Command: '%s' Status: %s err: '%s' out: '%s'" % \
                    (command, status, stderr_value, stdout_value)
            raise GitEngineError(status, stderr_value)

        return stdout_value

    def push(self, remote_branch, remote_path=None, local_branch=None):
        if not local_branch:
            local_branch = self.local_branch
        if not remote_path:
            remote_path = self.remote_path
        # Check if we can do fast-forward
        if not self.is_rebased(local_branch, "remotes/%s/%s" % \
                    (self.refs_name, remote_branch)):
            print "ERROR: Not able to push. " \
                  "Branch %s was not rebased to %s" % \
                  (local_branch, remote_branch)
            raise

        command = "git push %s %s:%s" % \
                (remote_path, local_branch, remote_branch)
        try:
            self.__exec(command)
        except GitEngineError as e:
            if e.status == 1:
                print "ERROR: Not able to push. " \
                      "Possible reason: Branch %s was not rebased to %s." % \
                      (local_branch, remote_branch)
            raise

    def remove_remote_branch(self, remote_branch, remote_path=None):
        if not remote_path:
            remote_path = self.remote_path
        self.__exec("git push %s :%s" % (remote_path, remote_branch))

    def fetch(self, remote_path=None, refs_name="origin"):
        if not remote_path:
            remote_path = self.remote_path
        self.refs_name = refs_name
        command = "git fetch -p " + remote_path
        # add refs definition
        command += " +refs/heads/*:refs/remotes/%s/*" % refs_name
        self.__exec(command)

    def submodule_init(self):
        command = "git submodule init"
        self.__exec(command)

    def submodule_update(self):
        command = "git submodule update"
        self.__exec(command)

    def wipe_all_submodules_helper(self):
        command = "for path in `git submodule status|cut -d' ' -f3`;" \
                  " do rm -rf $path; done"
        self.__exec(command)

    def cherry_pick(self, from_sha):
        command = "git cherry-pick %s" % from_sha

        self.__exec(command)

    def merge_fast_forward(self, branch_to_merge):
        command = "git merge %s --ff-only" % branch_to_merge
        self.__exec(command)

    def diff_commits(self, master_branch, slave_branch):
        """ return ordered (from older to newer) list of sha's"""
        command = "git log %s..%s" % (master_branch, slave_branch)
        command += " --pretty=format:%H"

        out = self.__exec(command)
        # if commits aren't found
        if out == "":
            return []
        # split commit shas to list
        commits = [line for line in out.split("\n")]
        return commits[::-1]

    def checkout_from_remote_branch(self, remote_branch, local_branch=None):
        command = "git checkout %s" % remote_branch
        if not local_branch:
            local_branch = self.local_branch
        else:
            # Store local_branch, we may need it later
            self.local_branch = local_branch
        command += " -b " + local_branch

        # Make sure we overwrite existing branch
        # Detaching HEAD to be able to remove branch we are currently on
        self.__exec("git checkout -f %s" % remote_branch)
        try:
            # Deleting branch
            self.__exec("git branch -D %s" % local_branch)
        except:
            # Exception is raised if there is no branch to delete
            pass
        self.__exec(command)

    def rebase(self, branch):
        self.__exec("rm -fr .git/rebase-apply")
        self.__exec("git rebase %s" % branch)

    def is_rebased(self, source, destination):
        if not source:
            source = self.local_branch
        # Get commits that differ between branches
        commits = self.diff_commits(destination, source)
        if not commits:
            # It means the branch has been rebased and fast-forwarded already
            return True
        # Check if parent of the first commit is refers to top dest. branch
        command = "git rev-parse %s^1" % commits[0]
        parent = self.__exec(command)
        if parent == "":
            raise GitEngineError(0, "Could not determine parent commit")

        head_in_dest = self.__exec("git rev-parse %s" % destination)

        if parent == head_in_dest:
            return True
        else:
            return False


class GitEngineError(Exception):

    def __init__(self, status, error):
        self.status = status
        self.error = error

    def __str__(self):
        return repr(self.status + " " + self.error)
