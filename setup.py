#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


install_requires = [
]

setup(
    name='mls-scraper',
    version='0.1',
    author='Mark Rogers',
    author_email='xxf4ntxx@gmail.com',
    url='http://github.com/f4nt/mls-scraper',
    description='Scraps stats from mlssoccer.com',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    include_package_data=True,
    entry_points={},
    test_suite='mls_scraper.tests',
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
