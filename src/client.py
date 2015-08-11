from __future__ import absolute_import
from gitlab import Gitlab
import git
from git.exc import GitCommandError
import os
import sys
import ConfigParser


class ProgressIndicator(git.objects.submodule.base.UpdateProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


def sync(projects):
    for p in projects:
        if p.archived:
            continue

        print("- {}".format(p.name))
        if not os.path.isdir(p.path):
            print(" "*4 + "cloning")

            repo = git.Repo.init(p.path)
            origin = repo.create_remote('gitlab', p.ssh_url_to_repo)
            assert origin.exists()
            assert origin == repo.remotes.gitlab == repo.remotes['gitlab']
            if not do_pull(repo):
                continue
            # Setup a local tracking branch of a remote branch
            ref = origin.refs[p.default_branch]
            repo.create_head(p.default_branch, ref).set_tracking_branch(ref)
            # checkout working copy
            repo.branches[p.default_branch].checkout()
        else:
           repo = git.Repo(p.path)
           pull(p)
        print(" "*4 + "updating")
        push(p)


def do_pull(repo):
    # assure we actually have data. fetch() returns useful information
    remote = repo.remotes.gitlab
    try:
        for fetch_info in remote.pull():
            print("Fetched %s to %s" % (fetch_info.ref, fetch_info.commit))
            print(fetch_info.note)
    except GitCommandError:
        print("Pull failed, is the repository empty?")
        return False
    return True


def push(project):
    repo = git.Repo(project.path)
    print("Pushing {p.name}".format(p=project))
    remote = repo.remotes.gitlab
    try:
        for info in remote.push():
            print("Pushed %s to %s" % (info.local_ref, info.remote_ref))
            print("Updated %s to %s" % (info.summary, info.flags))
    except GitCommandError:
        print("Push Failed")


def pull(project):
    # XXX check for dirty repo
    repo = git.Repo(project.path)
    print("Pulling {p.name}".format(p=project))
    if not do_pull(repo):
        return
    update_submodules(repo)


def update_submodules(repo):
    for sm in repo.submodules:
        sm.update()


def push_all(projects):
    local_repos(projects, push)


def pull_all(projects):
    local_repos(projects, pull)


def local_repos(projects, f):
    for p in projects:
        if not os.path.isdir(p.path):
            continue
        # check if it actually is a repo
        f(p)


def load_config():
    # XXX locate config file in the file system (current folder or above ?)
    parser = ConfigParser.ConfigParser()
    parser.read('gitlab.ini')
    return parser

def get_token():
    return os.getenv('GITLAB_TOKEN', config.get('gitlab', 'token'))

def get_projects(config):
    url = config.get('gitlab', 'url')
    gl = Gitlab(url, get_token)
    print("Connecting to Gitlab {}".format(url))
    gl.auth() # XXX catch exceptions
    user = gl.user
    print("Connected as {1} ({0})".format(user.name, user.username))
    group = gl.Group(config.get('gitlab', 'group')) # XXX catch exceptions
    return group.projects


COMMANDS = 'push pull sync'.split()
def main():
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        raise AttributeError("Command not supported")

    config = load_config()
    projects = get_projects(config)
    if cmd == 'sync':
        sync(projects)
    elif cmd == 'pull':
        pull_all(projects)
    elif cmd == 'push':
        push_all(projects)


if __name__ == '__main__':
    main()
