# merge-fs
Fuse file system is able to merge multiple folders in one unique folder.

```
usage: /home/michael/dev/merge-fs/venv/bin/merge-fs <mountpoint> [<dir> [<dir> ...]]
```


## Virtualenv inheritance

You can use merge-fs to make multiple virtualenvs inherit each other packages.

```
$> virtualenv venvA
New python executable in venvA/bin/python
Installing setuptools, pip, wheel...done.
$> virtualenv venvB
New python executable in venvA/bin/python
Installing setuptools, pip, wheel...done.
$> mkdir venvC
# Start the filesystem in an other terminal.
$> merge-fs venvC venvB venvA
# Get back to previous terminal
# install a tornado on venvA
$> venvA/bin/pip install -q tornado
# install a jinja2 on venvB
$> venvA/bin/pip install -q jinja2
$> venvC/bin/python -c "import tornado, jinja2"
$>
```
