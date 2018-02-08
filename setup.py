from setuptools import setup

setup(name='dkb_robo',
    version='0.4',
    description='library to access the internet banking area of "Deutsche Kreditbank" to get account information and transactions.',
    url='https://github.com/grindsa/dkb-robo',
    author='grindsa',
    author_email='grindelsack@gmail.com',
    license='GPL',
    packages=['dkb_robo'],
    install_requires=[
        'mechanize',
        'bs4',
        'html5lib',
        'six'
    ],
    zip_safe=False)