""" setup.py """
from pathlib import Path
from setuptools import setup

this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

setup(name='dkb_robo',
    version='0.27',
    description='library to access the internet banking area of "Deutsche Kreditbank" to get account information and transactions.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/grindsa/dkb-robo',
    author='grindsa',
    author_email='grindelsack@gmail.com',
    license='GPL',
    packages=['dkb_robo'],
    platforms='any',
    install_requires=[
        'mechanicalsoup',
        'bs4',
        'html5lib',
        'six',
        'tabulate',
        'click'
    ],
    entry_points={
        "console_scripts": ["dkb=dkb_robo.cli:main"],
    },
    extras_require={
        "cli": ["click", "tabulate"],
    },
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: German',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
        ],
    zip_safe=False,
    test_suite="test")
