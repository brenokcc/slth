import os
from setuptools import find_packages, setup

install_requires = open('requirements.txt').read().splitlines()

setup(
    name='pyslth',
    version='0.3.7',
    packages=find_packages(exclude=('xxx', 'xxx.*')),
    install_requires=install_requires,
    extras_require={
        'dev': []
    },
    include_package_data=True,
    license='BSD License',
    description='API generator based on yml file',
    long_description='',
    url='https://github.com/brenokcc',
    author='Breno Silva',
    author_email='brenokcc@yahoo.com.br',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
