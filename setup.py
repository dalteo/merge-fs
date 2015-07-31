#!/usr/bin/env python
import os
import fnmatch
from distutils.core import setup
from pip.req import parse_requirements
import pip.download

package_root = os.path.dirname(os.path.abspath(__file__))

install_reqs = parse_requirements(os.path.join(package_root, 'requirements.txt'), session=pip.download.PipSession())

reqs = [str(ir.req) for ir in install_reqs]

entry_points = {
    'console_scripts': [
        'merge-fs = merge_fs:main',
    ],
}

exclude_patterns = [
    '*~',
]

setup(
    name='fluxo-agency',
    version='1.0',
    description="",
    author="Fluxo Agency",
    author_email="fluxoagency@gmail.com",
    maintainer="Delaporte Michael",
    maintainer_email="michael@vfx-delaporte.com",
    py_modules=['merge_fs'],
    install_requires=reqs,
    entry_points=entry_points,
    include_package_data=True,
)

