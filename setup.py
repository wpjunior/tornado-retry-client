# -*- coding:utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='tornado-retry-client',
    version='0.4.5',
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
    extras_require={
        'tests': [
            'mock',
            'nose',
            'coverage',
            'flake8',
            'yanc',
            'bumpversion',
        ]
    }
)
