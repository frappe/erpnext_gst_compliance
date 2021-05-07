# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in erpnext_e_invoicing/__init__.py
from erpnext_e_invoicing import __version__ as version

setup(
	name='erpnext_e_invoicing',
	version=version,
	description='Make ERPNext E-Invoice Compliant',
	author='Frappe',
	author_email='developers@erpnext.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
