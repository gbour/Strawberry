# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010, Guillaume Bour <guillaume@bour.cc>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""
from twisted.web     import server
from mother.callable import Callable, callback

from data      import *

from tentacles        import Object
from tentacles.fields import *
from tentacles.queryset import filter


class Link(Object, Callable):
	__stor_name__ = 'delicious__link'

	id            = Integer(pk=True, autoincrement=True)
	link          = String(unique=True, allow_none=False)
	name          = String()
	description   = String()
	stars         = Integer(default=0)
	valid         = Boolean(default=False)
	creation      = Datetime(default='now')
	last_change   = Datetime()
	last_check    = Datetime()
	icon          = Binary()
	screenshot    = Binary()
	
	tags          = ReferenceSet(Tag)


	def GET(self, id):
		link = list(filter(lambda x: x.id == id, Link))
		if len(link) == 0:
			return (404, None)

		link = link[0]
		res  = {}
		for name, fld in link.__fields__.iteritems():
			if isinstance(fld, Reference):
				continue

			res[name] = getattr(link, name)
			#TODO: should be done in a generic way
			# the best way should probably be to have a tentacles json backend
			# For that, we need to be able to switch backend for an object
			
			# JSON encoder should also understand datetime object
			if isinstance(fld, Datetime) and res[name] is not None:
				res[name] = str(res[name])

		res['tags'] = []
		for tag in link.tags:
			res['tags'].append({'id': tag.id, 'tag': tag.tag})

		return res

	def PUT(self, content):
		if 'link' not in content or 'name' not in content:
			return (400, "link, name are mandatory keys")
		
		if 'id' in content and len(filter(lambda x: x.id == content['id'], Link)) > 0:
			return (400, "id already exists")
		if len(filter(lambda x: x.link == content['link'], Link)) > 0:
			return (400, "name must be unique")

		link = Link()
		for key, value in content.iteritems():
			if key == 'tags':
				continue

			if not key in link.__fields__:
				return(409, "unknown field '%s'" % key)
				
			setattr(link, key, value)

		"""We query all tags (by tagname), and create new ones"""
		if 'tags' in content:
			link.tags = list(filter(lambda t: t.tag in content['tags'], Tag))
			link.tags.extend([Tag(tag=t) for t in content['tags'] if t not in [tag.tag for tag in link.tags]])

		link.save()
		return link.id

	def DELETE(self, id):
		"""
		
			NOTE: associated tags, even if specially created for this link, are not deleted
		"""
		links = list(filter(lambda x: x.id == id, Link))
		if len(links) == 0:
			return (404, "not found")
		elif len(links) > 1:
			return (500, "return several links for the same id")

		print 'ZOZ', id, links
		links[0].delete()
		return (200, True)

	@callback(name='icon', method=['GET', 'PUT', 'DELETE'])
	def _icon(self, request, id, content=None):
		return self._binary('icon', request, id, content)

	@callback(name='screenshot', method=['GET', 'PUT', 'DELETE'])
	def _screenshot(self, request, id, content=None):
		return self._binary('screenshot', request, id, content)

	def _binary(self, field, request, id, content):
		link = list(filter(lambda x: x.id == id, Link))
		if len(link) == 0:
			return (404, None)
		link = link[0]

		if request.method == 'PUT':
			setattr(link, field, content.read())
			print 'LNK=', link, link.id
			link.save()
			print(list(filter(lambda x: x.id == id, Link)))

			return None

		elif request.method == 'DELETE':
			setattr(link, field, None)
			link.save()
			return None

		# GET
		data = getattr(link, field)
		if data is None:
			return (204, None)

		import magic
		m = magic.open(magic.MAGIC_MIME)
		m.load()
		mime = m.buffer(data)
		m.close()

		if mime is not None and len(mime) > 0:
			request.setHeader('Content-Type', mime.split(';')[0])
		request.write(str(getattr(link, field)))
		request.finish()
		
		return server.NOT_DONE_YET

	@callback
	def all(self):
		res = map(lambda x: x.id, Link)
		print res
		return res

	@callback
	def bytag(self, tagname):
		res = list(filter(lambda x: tagname in [name for tag in x.tags], Link))
		print res
		return res


