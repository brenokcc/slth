import os
from setuptools import find_packages, setup

install_requires = []

setup(
    name='slthcore',
    version='0.2.4',
    packages=find_packages(),
    install_requires=install_requires,
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
