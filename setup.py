# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in frappe_state_management/__init__.py
from frappe_state_management import __version__ as version

setup(
	name='frappe_state_management',
	version=version,
	description='State Management Architecture for Handling Updates on Documents',
	author='Leam Technology Systems',
	author_email='admin@leam.ae',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
