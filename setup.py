from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

cur_dir = path.abspath(path.dirname(__file__))

with open(path.join(cur_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='BayesBall',
    version='0.1.0.dev1',
    description='A small collection of ',
    long_description=long_description,
    url='https://github.com/chris-french/bayesball',
    author='Christopher F. French',
    author_email='chris.french.writes@gmail.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console :: Curses',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research'
        'Topic :: Scientific/Engineering',
        'Topic :: Games/Entertainment :: Simulation',
        'Programming Language :: Python :: 3 :: Only'
    ],
    keywords='baseball simulation probability',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['numpy'],
    python_requires='>=3'
)