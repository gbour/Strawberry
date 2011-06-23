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

from setuptools                      import setup, Command
from setuptools.command.install_lib  import install_lib
from distutils.dir_util              import ensure_relative
from distutils.util                  import convert_path, change_root
from setuptools.dist                 import Distribution
from setuptools.command.install      import install

class _Distribution(Distribution):
	def __init__(self, *args, **kwargs):
		# add new option for motherapps
		self.motherapps = []

		Distribution.__init__(self, *args, **kwargs)

		# automatically install our install_lib version
		if not 'install' in self.cmdclass:
			self.cmdclass['install']= _install
		if not 'install_lib' in self.cmdclass:
			self.cmdclass['install_lib']= _install_lib

	def has_pure_modules(self):
		"""Ensure install_lib.run() is executed even if we have no python modules
		"""
		return True


class _install(install):
	def _fix_paths(self):
		self.install_apps = self.install_base
		# manage --prefix option (i.e is set when in an environment created with *virtualenv*)
		if self.prefix_option is None and self.install_base == '/usr': # default prefix
			# TODO: specific install paths may not be changes if explicitly specified by user on command line (--install-scripts and --install-data options)
			(self.install_scripts, self.install_data, self.install_apps) = ('/usr/bin', '/', '/')

		# manage --root option (is set when doing "setup.py bdist")
		if self.root is not None:
			for p in ('scripts','data','apps'):
				setattr(self, 'install_'+p, os.path.join(self.root, ensure_relative(getattr(self, 'install_'+p))))
		
	def finalize_options(self):
		install.finalize_options(self)
		self._fix_paths()

	def run(self):
		self._fix_paths()
		install.run(self)


class _install_lib(install_lib):
	excludes = ['.svn']
	dest     = 'var/lib/mother/apps'
	_pyfiles = []

	def run(self):
		if self.dry_run or len(self.distribution.motherapps) == 0:
			return

		inst = self.get_finalized_command('install')

		for app in self.distribution.motherapps:
			self._copy_tree(
				os.path.join(*app.split('.')), 
				os.path.join(inst.install_apps, self.dest)
			)

		self.byte_compile(self._pyfiles)
		#do not copy webapp in python standard directory
		#install_lib.run(self)

	def _copy_tree(self, src, dst):
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

			[self._copy_file(os.path.join(root, f), os.path.join(_dst, f)) for f in files if f not in _excl]

	def _copy_file(self, src, dst):
		install_lib.copy_file(self,src, dst)
		if dst.endswith('.py'):
			self._pyfiles.append(dst)


setup(
	name         = 'strawberry',
	version      = '0.1.0',
	description  = 'WebApp - Web links bookmark',
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

	long_description = """Strawberry is a links bookmarking self-hosted service.
		It allows you to store, manage, classify and consult your preferred links from
		anywhere.

		Strawberry is self-hosted, meaning you need a server to host your strawberry
		instance.
		Strawberry is written in python, as a *Mother* WebApp
	""",

	install_requires = ['magic >= 0.1', 'mother-webapps-framework >= 0.1.0, < 0.2'],

	distclass   = _Distribution,
	motherapps  = ['strawberry'],
)

