""" setup.py """
from setuptools import setup
setup(name='dkb_robo',
    version='0.18',
    description='library to access the internet banking area of "Deutsche Kreditbank" to get account information and transactions.',
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
        'six'
    ],
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
