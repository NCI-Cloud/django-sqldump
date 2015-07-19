import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name = 'django-sqldump',
    version = 'dev',
    packages = ['sqldump'],
    include_package_data = True,
    description = 'dump sql query results',
    long_description = README,
    install_requires = [
        'django >=1.8.3',
        'lxml >=3.4.4',
    ],
)
