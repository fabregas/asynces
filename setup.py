import os
import sys
from setuptools import setup


install_requires = ['aiohttp']

PY_VER = sys.version_info

if PY_VER < (3, 5):
    raise RuntimeError("asynces doesn't suppport Python earlier than 3.5")


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


def read_version():
    ver = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(ver) as f:
        return f.read().strip()

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
