# coding: utf-8

import os
import pwd
import errno
import shutil

from subprocess import check_call


def get_uid(name):
    return pwd.getpwnam(name).pw_uid if isinstance(name, basestring) else name


def get_gid(name):
    return pwd.getpwnam(name).pw_gid if isinstance(name, basestring) else name


def ensure_dir(path, owner='root', group='root', mode=0755):
    try:
        os.mkdir(path, mode)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    os.chown(path, get_uid(owner), get_gid(group))


def ensure_dir_recursive(topdir, path, owner='root', group='root', mode=0755):
    # Create dirs recursively, but not above topdir, which must exist before
    if topdir == path:
        # Stop here, not above
        return
    if not path.startswith(topdir):
        return

    # Make sure our parent exists
    parent = os.path.dirname(path)
    if not os.path.exists(parent):
        ensure_dir_recursive(topdir, parent, owner, group, mode)
    ensure_dir(path, owner, group, mode)


def ensure_dir_absent(path):
    if os.path.lexists(path):
        if os.path.islink(path):
            os.unlink(path)
        else:
            # NOTES: If path is a regular file, it's still not deleted
            shutil.rmtree(path, ignore_errors=True)


def ensure_app_user(appname, uid):
    username = 'dae_%s' % appname
    try:
        pwd.getpwnam(username)
    except KeyError:
        check_call(['/usr/sbin/useradd', '--user-group', '--create-home',
                    '--uid', str(uid),
                    '--shell', '/sbin/nologin',
                    '--comment', 'created by dae system',
                    '--home-dir', '/var/dae/home/%s' % appname,
                    username])


def ensure_dirs(paths, owner='root', group='root', mode=0755):
    for path in paths:
        ensure_dir(path, owner=owner, group=group, mode=mode)


def ensure_file(path, owner='root', group='root', mode=0644, content=''):
    try:
        current_content = open(path).read()
    except IOError, e:
        if e.errno == errno.ENOENT:
            current_content = None
        else:
            raise

    if current_content != content:
        with open(path, 'w') as f:
            f.write(content)

    os.chmod(path, mode)
    os.chown(path, get_uid(owner), get_gid(group))


def ensure_file_absent(path, notify=None):
    if os.path.lexists(path):
        os.unlink(path)


def ensure_link(path, target, owner='root', group='root'):
    if os.path.lexists(path) and \
            not (os.path.islink(path) and os.readlink(path) == target):
        os.unlink(path)

    if not os.path.lexists(path):
        os.symlink(target, path)
