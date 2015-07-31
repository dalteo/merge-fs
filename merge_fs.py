#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import shutil
import errno

from fuse import FUSE, FuseOSError, Operations


class MergeFS(Operations):
    """Example memory filesystem. Supports only one level of files."""
    
    def __init__(self, mnt, roots):
        self._mnt = mnt
        self._roots = roots
    
    def _full_path(self, filename, mode='r'):
        value = None
        if filename.startswith('/'):
            filename = filename[1:]

        for root in self._roots:
            p = os.path.join(root, filename)
            if os.path.exists(p):
                value = p
                break
        if value is None:
            value = os.path.join(self._roots[0], filename)
        if mode == 'r':
            return value
        elif mode == 'w':
            return os.path.join(self._roots[0], filename)
        elif mode == 'rw':
            if not value.startswith(self._roots[0]):
                new_value = os.path.join(self._roots[0], filename)
                shutil.copy(value, new_value)
                value = new_value
            return value
        else:
            raise ValueError("Unknown mode %s."%mode)
    
    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path, mode='r')
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path, mode='rw')
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path, mode='rw')
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path, mode='r')
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        dirents = [
            '.',
            '..',
        ]
        if path.startswith('/'):
            path = path[1:]
        for root in self._roots:
            full_path = os.path.join(root, path)
            if not os.path.isdir(full_path):
                continue
            for f in os.listdir(full_path):
                if not f in dirents:
                    dirents.append(f)
                    yield f

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path, mode='r'))
        #pathname = self._full_path(pathname, mode='r')
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            if pathname.startswith(self._mnt):
                return os.path.relpath(pathname, self._mnt)
            else:
                return pathname
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path, mode='w'), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        if full_path.startswith(self._roots[0]):
            raise IOError("Operation not permited.")
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path, mode='w'), mode)

    def statfs(self, path):
        full_path = self._full_path(path, mode='r')
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        filename = self._full_path(path, mode='r')
        if filename.startswith(self._roots[0]):
            raise IOError("Operation not permited.")
        return os.unlink(filename)

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target, mode='w'))

    def rename(self, old, new):
        src = self._full_path(old, mode='r')
        if src.startswith(self._roots[0]):
            raise IOError("Operation not permited.")
        return os.rename(src, self._full_path(new, mode='w'))

    def link(self, target, name):
        return os.link(self._full_path(target, mode='r'), self._full_path(name, mode='w'))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path, mode='rw'), times)

    # File methods
    # ============
    
    # Flags:
    # os.O_APPEND 1024 0x400 0b10000000000
    # os.O_ASYNC 8192 0x2000 0b10000000000000
    # os.O_CREAT 64 0x40 0b1000000
    # os.O_DIRECT 16384 0x4000 0b100000000000000
    # os.O_DIRECTORY 65536 0x10000 0b10000000000000000
    # os.O_DSYNC 4096 0x1000 0b1000000000000
    # os.O_EXCL 128 0x80 0b10000000
    # os.O_LARGEFILE 0 0x0 0b0
    # os.O_NDELAY 2048 0x800 0b100000000000
    # os.O_NOATIME 262144 0x40000 0b1000000000000000000
    # os.O_NOCTTY 256 0x100 0b100000000
    # os.O_NOFOLLOW 131072 0x20000 0b100000000000000000
    # os.O_NONBLOCK 2048 0x800 0b100000000000
    # os.O_RDONLY 0 0x0 0b0
    # os.O_RDWR 2 0x2 0b10
    # os.O_RSYNC 1052672 0x101000 0b100000001000000000000
    # os.O_SYNC 1052672 0x101000 0b100000001000000000000
    # os.O_TRUNC 512 0x200 0b1000000000
    # os.O_WRONLY 1 0x1 0b1
    
    def open(self, path, flags):
        r = ''
        w = ''
        if flags & os.O_APPEND:
            r = 'r'
            w = 'w'
        if flags & os.O_CREAT:
            w = 'w'
        if flags & os.O_WRONLY:
            w = 'w'
            r = ''
        if flags & os.O_RDONLY:
            w = ''
            r = 'r'
        if flags & 0x48000:
            w = ''
            r = 'r'
        
        
        mode = '%s%s'%(r, w)
        if mode == '':
            raise Exception("Unknown flag %s %s %i for path %s."%(bin(flags), hex(flags), flags, path))
        full_path = self._full_path(path, mode=mode)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path, mode='w')
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path, mode='r')
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
        
def main():
    argv = sys.argv
    if len(argv) < 3:
        print('usage: %s <mountpoint> [<dir> [<dir> ...]]' % argv[0])
        exit(1)
    fuse = FUSE(MergeFS(argv[1], argv[2:]), argv[1], foreground=True)

if __name__ == "__main__":
    main()
