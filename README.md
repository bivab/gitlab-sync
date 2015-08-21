# gitlab-sync

Utility to synchronize a GitLab group of repositories at once.

# Installation

To get the latest stable version use (with the git tag of the version you wish to install):

`[sudo] pip install git+http://tuatara.cs.uni-duesseldorf.de/bivab/gitlab-sync.git@0.0.1`

# Usage

## Initialisation

Run `gitlab-sync init` in the directory where you want to checkout all
projects, this will create a gitlab.ini file that you need to edit for your
setup:

* Set `url` to the URL of your GitLab instance.
* Set `group` to the group you want to check out.
* Set `token` to your personal GitLab API-Token or export it as an environment
  variable named `GITLAB_TOKEN`.


## Sync

`gitlab-sync [sync]` will clone, push to and pull from all repositories in the
requested group.

`gitlab-sync pull` will only pull changes from the GitLab instance to already
cloned repositories.

`gitlab-sync push` will only push changes to the GitLab instance.
