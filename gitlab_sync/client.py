from __future__ import absolute_import
from gitlab import Gitlab, GitlabConnectionError
import git
from git.exc import GitCommandError
import os
import sys
import ConfigParser
from .log import getLogger


logger = getLogger()

DEFAULT_REMOTE = 'gitlab'

class ProgressIndicator(git.objects.submodule.base.UpdateProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


def sync(projects, config):
    for p in projects:
        if p.archived:
            continue

        logger.info("Repository {}".format(p.name))

        protocol = config.get('gitlab', 'protocol')
        if protocol == 'ssh':
            url = p.ssh_url_to_repo
        else:
            logger.info("Using ssh-key authentication is recommended to "
                        "avoid entering your password "
                        "for each repository and request")
            url = p.http_url_to_repo

        if not os.path.isdir(p.path):
            logger.info("Cloning")

            repo = git.Repo.init(p.path)
            create_remote(repo, url)

            if not do_pull(repo):
                continue
            # Setup a local tracking branch of a remote branch
            ref = origin.refs[p.default_branch]
            repo.create_head(p.default_branch, ref).set_tracking_branch(ref)
            logger.debug("Creating local branch {} as remote tracking branch".format(p.default_branch))
            # checkout working copy
            repo.branches[p.default_branch].checkout()
            logger.debug("Checked out branch {}".format(p.default_branch))
        else:
            repo = git.Repo(p.path)
            # check if 'gitlab' remote exists
            try:
                repo.remote(DEFAULT_REMOTE)
            except ValueError:
                logger.warning('Repository does not have a {} remote, adding it.'.format(DEFAULT_REMOTE))
                create_remote(repo, url)

            if not pull(p):
                continue
            logger.info("Updating")
            push(p)


def create_remote(repo, url):
    origin = repo.create_remote(DEFAULT_REMOTE, url)
    assert origin.exists()
    assert origin == repo.remote(DEFAULT_REMOTE) == repo.remotes[DEFAULT_REMOTE]

def do_pull(repo):
    # assure we actually have data. fetch() returns useful information
    remote = repo.remotes.gitlab
    try:
        if repo.is_dirty():
            logger.warning("Repository is dirty -- fetching updates, please merge manually")
            fetch_info = remote.fetch()
        elif len(repo.refs) == 0: # emtpy repo
            logger.info("Empty repository, add some commits.")
            return False
        else:
            fetch_info = remote.pull()
    except GitCommandError:
        logger.warning("""Fetching failed, possible reasons:\n"""
                        """* The umpstream repository is empty.\n"""
                        """* The provided credentials are wrong.""")
        return False

    for fetch_info in fetch_info:
        logger.info("Fetched %s to %s" % (fetch_info.ref, fetch_info.commit))
        logger.info(fetch_info.note)
    return True


def push(project):
    repo = git.Repo(project.path)
    logger.info("Pushing {p.name}".format(p=project))
    remote = repo.remotes.gitlab
    try:
        for info in remote.push("{0}:{0}".format(project.default_branch)):
            logger.info("Pushed %s to %s" % (info.local_ref, info.remote_ref))
            logger.info("Updated %s to %s" % (info.summary, info.flags))
    except GitCommandError:
        logger.warning("Push Failed")


def pull(project):
    repo = git.Repo(project.path)
    logger.info("Pulling {p.name}".format(p=project))
    if not do_pull(repo):
        return False
    update_submodules(repo)
    return True


def update_submodules(repo):
    for sm in repo.submodules:
        logger.debug("Updating submodule {}".format(sm.name))
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
    if not os.path.exists('gitlab.ini'):
        raise ValueError("gitlab.ini not found")
    parser = ConfigParser.ConfigParser()
    parser.read('gitlab.ini')
    return parser

def get_token(config):
    return os.getenv('GITLAB_TOKEN', config.get('gitlab', 'token'))

def get_projects(config):
    url = config.get('gitlab', 'url')
    gl = Gitlab(url, get_token(config))
    logger.debug("Connecting to Gitlab {}".format(url))
    gl.auth() # XXX catch exceptions
    user = gl.user
    logger.info("Connected as {1} ({0})".format(user.name, user.username))
    group = gl.Group(config.get('gitlab', 'group')) # XXX catch exceptions
    return group.projects


def init():
    if os.path.exists('gitlab.ini'):
        logger.warning("found gitlab.ini, project already initialized.")
        return
    # XXX sample should go in MANIFEST ?
    sample = os.path.join(os.path.dirname(__file__), 'gitlab.ini.sample')
    with open(sample, 'r') as sample:
        with open('gitlab.ini', 'w') as inifile:
            inifile.write(sample.read())
    logger.info("Created gitlab.ini configuration file in currenct directory.")
    logger.info("Add your GitLab token to gitlab.ini before running gitlab-sync.")


COMMANDS = 'init push pull sync'.split()
def main():
    try:
        cmd = sys.argv[1]
        if cmd not in COMMANDS:
            logger.error("Command not supported, valid commands are init, "
                            "sync, pull and push")
            return
    except IndexError:
        cmd = 'sync'

    if cmd == 'init':
        init()
        return

    try:
        config = load_config()
    except ValueError:
        logger.error("gitlab.ini configuration file not found.")
        return init()
    try:
        projects = get_projects(config)
    except GitlabConnectionError as e:
        logger.error(e.error_message)
        return

    if cmd == 'sync':
        sync(projects, config)
    elif cmd == 'pull':
        pull_all(projects)
    elif cmd == 'push':
        push_all(projects)
    logger.info("Done.")


if __name__ == '__main__':
    main()
