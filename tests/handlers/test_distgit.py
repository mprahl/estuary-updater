# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import json
from os import path

from estuary.models.distgit import DistGitCommit, DistGitBranch, DistGitRepo

from tests import message_dir
from estuary_updater.handlers.distgit import DistGitHandler
from estuary.models.bugzilla import BugzillaBug
from estuary_updater import config
from estuary.models.user import User


def test_distgit_new_commit():
    """Test the dist-git handler when it recieves a new commit message."""
    with open(path.join(message_dir, 'distgit', 'distgit_commit.json'), 'r') as f:
        msg = json.load(f)

    assert DistGitHandler.can_handle(msg) is True
    handler = DistGitHandler(config)
    handler.handle(msg)

    commit = DistGitCommit.nodes.get_or_none(hash_='2cc7f45c8aae163feed162478622f5f9165c8e78')
    assert commit is not None

    # Check that all properties were appropriately stored
    assert commit.hash_ == '2cc7f45c8aae163feed162478622f5f9165c8e78'
    log_msg = ('Layer: Fix memleaks\n\nResolves: rhbz1534646, rhbz1484051\nRelated: #1234567, '
               'rhbz#2345678\n')
    assert commit.log_message == log_msg
    assert commit.author.get().username == 'emusk'
    assert commit.author.get().email == 'emusk@redhat.com'
    assert commit.branches[0].name == 'rhel-7.6'
    assert commit.branches[0].repo_namespace == 'rpms'
    assert commit.branches[0].repo_name == 'openldap'
    assert commit.repos[0].name == 'openldap'
    assert commit.repos[0].namespace == 'rpms'

    bug = BugzillaBug.nodes.get_or_none(id_='1534646')
    bug2 = BugzillaBug.nodes.get_or_none(id_='1484051')
    bug_related = BugzillaBug.nodes.get_or_none(id_='1234567')
    bug_related2 = BugzillaBug.nodes.get_or_none(id_='2345678')
    repo = DistGitRepo.nodes.get_or_none(name='openldap')
    branch = DistGitBranch.nodes.get_or_none(name='rhel-7.6')
    author = User.nodes.get_or_none(username='emusk')

    # Check that relationships are connected
    assert repo.contributors.is_connected(author)
    assert repo.branches.is_connected(branch)
    assert repo.commits.connect(commit)
    assert branch.contributors.is_connected(author)
    assert branch.commits.connect(commit)
    assert commit.resolved_bugs.is_connected(bug)
    assert commit.resolved_bugs.is_connected(bug2)
    assert len(commit.resolved_bugs.all()) == 2
    assert commit.related_bugs.is_connected(bug_related)
    assert commit.related_bugs.is_connected(bug_related2)
    assert len(commit.related_bugs.all()) == 2
    assert not commit.reverted_bugs.all()
