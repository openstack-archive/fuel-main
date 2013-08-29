git-helper
==========

git_api.py is wrapper on git subcommands,
    the code was inspired by https://github.com/alekseiko/autoMaster,
    but significally rewritten.

Usage example:

```python
>>> import git_api
>>> engine = git_api.GitEngine()
Executing command git status in cwd=test-repo
Executing command mkdir test-repo in cwd=.
Executing command git init in cwd=test-repo
>>> engine.fetch()
Executing command git fetch git@github.com:mihgen/test-repo.git +refs/heads/*:refs/remotes/origin/* in cwd=test-repo
>>> commits = engine.diff_commits("remotes/origin/master", "remotes/origin/newbr")
Executing command git log remotes/origin/master..remotes/origin/newbr --pretty=format:%H in cwd=test-repo
>>> commits
['ebe7d216a3ad2268693946d122eff14fb2986051']
>>> engine.checkout_from_remote_branch("remotes/origin/master")
Executing command git branch -D temp-for-engine in cwd=test-repo
ERRRO: Command: 'git branch -D temp-for-engine' Status: 1 err: 'error: branch 'temp-for-engine' not found.' out: ''
Executing command git checkout remotes/origin/master -b temp-for-engine in cwd=test-repo
>>> 
>>> for sha in commits:
...     engine.cherry_pick(sha)
... 
Executing command git cherry-pick ebe7d216a3ad2268693946d122eff14fb2986051 in cwd=test-repo
>>> engine.push("master")
Executing command git push git@github.com:mihgen/test-repo.git temp-for-engine:master in cwd=test-repo
```
