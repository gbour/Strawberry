#!/usr/bin/env python
# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as
	published by the Free Software Foundation, version 3.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os, os.path

from distutils.core                 import setup
from distutils.command.install_lib  import install_lib
from distutils.command.install_data import install_data
from distutils.util                 import convert_path, change_root

class _install_lib(install_lib):
	def finalize_options(self):
		"""Copy python files in Mother apps/ directory instead of standard python dirs
		"""
		install_lib.finalize_options(self)
		self.install_dir = os.path.join(self.get_finalized_command('bdist_dumb').bdist_dir, 'var/lib/mother/apps')


class _install_data(install_data):
	"""Allow use of directories as data_file sources
	"""
	excludes = ['.svn']

	def run(self):
		self.mkpath(self.install_dir)

		for f in self.data_files:
			if not isinstance(f, (list, tuple)):
				continue

			dir = convert_path(f[0])
			if not os.path.isabs(dir):
				dir = os.path.join(self.install_dir, dir)
			elif self.root:
				dir = change_root(self.root, dir)
			self.mkpath(dir)

			for data in f[1]:
				if os.path.isdir(data):
					self.copy_tree(data, dir)
					f[1].remove(data)
					
		install_data.run(self)

	def copy_tree(self, src, dst):
		"""We replace Command.copy_tree() as we need to exclude .svn directories
		"""	
		_excl = list(self.excludes)

		# we keep only the last dir of src path
		dststart = len(src.split(os.sep))-1 
		self.mkpath(os.path.join(dst, *src.split(os.sep)[dststart:]))

		for root, dirs, files in os.walk(src):
			if root in _excl:
				[_excl.append(os.path.join(root,d)) for d in dirs]; continue

			_dst = os.path.join(dst, *root.split(os.sep)[dststart:])
			for d in dirs:
				if d in _excl:
					_excl.append(os.path.join(root, d))
				else:
					self.mkpath(os.path.join(_dst, d))

			[self.copy_file(os.path.join(root, f), os.path.join(_dst, f)) for f in files if f not in _excl]


setup(
	name         = 'strawberry',
	version      = '0.1.0',
	description  = 'WebApp - Web links manager',
	author       = 'Guillaume Bour',
	author_email = 'guillaume@bour.cc',
	url          = 'http://devedge.bour.cc/wiki/Strawberry/',
	license      = 'GNU Affero General Public License v3',
	classifiers  = [
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Environment :: Plugins',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: GNU Affero General Public License v3',
		'Natural Language :: English',
		'Natural Language :: French',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.5',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Topic :: Internet',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	],

	long_description = """""",


	packages    = ['strawberry'],
	data_files  = [('/var/lib/mother/apps/strawberry', ['strawberry/templates'])],
	requires    = ['magic (>= 0.1)', 'mother (>= 0.1.0, < 0.2)'],

	cmdclass    = {
		'install_lib' : _install_lib,
		'install_data': _install_data,
	}
)

