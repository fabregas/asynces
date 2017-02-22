import os
import re
import sys
from setuptools import setup


install_requires = ['aiohttp']

PY_VER = sys.version_info

if PY_VER < (3, 5):
    raise RuntimeError("asynces doesn't suppport Python earlier than 3.5")


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrcdev]+)'")
    init_py = os.path.join(os.path.dirname(__file__), 'asynces', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            raise RuntimeError('Cannot find version in asynces/__init__.py')

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Intended Audience :: Developers',
    'Programming Language :: Python :: 3.5',
    'Operating System :: OS Independent',
    'Topic :: System :: Networking',
    'Topic :: System :: Distributed Computing',
    'Development Status :: 4 - Beta',
]


setup(name='asynces',
      version=read_version(),
      description=('asyncio driver for elasticsearch'),
      long_description=read('README.md'),
      classifiers=classifiers,
      platforms=['POSIX'],
      author='Kostiantyn Andrusenko',
      author_email='kksstt@gmail.com',
      url='https://github.com/fabregas/asynces/',
      download_url='https://pypi.python.org/pypi/asynces',
      license='Apache 2',
      packages=['asynces'],
      install_requires=install_requires,
      include_package_data=True)
