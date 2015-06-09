# -*- coding:utf-8 -*-

from setuptools import find_packages, setup

version = '0.2.0'

setup(
    name='tornado-retry-client',
    version=version,
    description='Simple retry tornado http client',
    long_description='',
    classifiers=[],
    keywords='tornado retry client',
    author='Wilson Júnior',
    author_email='wilsonpjunior@gmail.com',
    url='https://github.com/wpjunior/tornado-retry-client',
    license='MIT',
    include_package_data=True,
    packages=find_packages(exclude=["tests", "tests.*"]),
    platforms=['any'],
    install_requires=[
        'tornado',
    ],
    test_suite='nose.collector',
    tests_require=[
        'mock',
        'nose',
        'coverage'
    ]
)
