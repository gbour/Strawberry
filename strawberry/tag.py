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
from twisted.web     import server
from mother.callable import Callable, callback, LoopbackSelf as self
from mother          import routing

from tentacles          import Object
from tentacles.fields   import *
from tentacles.queryset import filter, map, len

class Tag(Object, Callable):
	__stor_name__ = 'strawberry__tag'

	id            = Integer(pk=True, autoincrement=True)
	name          = String(unique=True, allow_none=False)
	description   = String()

	def GET(self, id, **kwargs):
		tag = list(filter(lambda x: x.id == id, Tag))
		if len(tag) == 0:
			return (404, None)

		tag = tag[0]
		res  = {}
		for name, fld in tag.__fields__.iteritems():
			if isinstance(fld, Reference):
				continue

			res[name] = getattr(tag, name)

		return res

	def PUT(self, content):
		if 'name' not in content:
			return (400, "*name* key is mandatory")
		
		if 'id' in content and len(filter(lambda x: x.id == content['id'], Tag)) > 0:
			return (400, "id already exists")
		if len(filter(lambda x: x.link == content['name'], Tag)) > 0:
			return (400, "name must be unique")

		tag = Tag()
		for key, value in content.iteritems():
			if not key in tag.__fields__:
				return(409, "unknown field '%s'" % key)
				
			setattr(tag, key, value)
		tag.save()
		return tag.id

	def DELETE(self, id):
		"""
		
			NOTE: associated tags, even if specially created for this link, are not deleted
		"""
		tags = list(filter(lambda x: x.id == id, Tag))
		if len(tags) == 0:
			return (404, "not found")
		elif len(tags) > 1:
			return (500, "return several tags for the same id")

		tags[0].delete()
		return (200, True)

	@callback
	def all(self):
		return list(map(lambda x: x.id, Tag))

	"""
		bytag is not one of GET,POST,PUT,DELETE method, it does not take default class
		ctype
	"""
	"""
	#@callback(url='/{tag}', content_type='internal/python', modifiers={'text/html': self.html_bytag})
	def bytag(self, tag, **kwargs):
		#return "search tag by name= %s" % tagQ
		errors = {}
		if len(tag) == 0:
			errors['tag'] = (10, 'field required')
			return routing.HTTP_400(errors) # bad request

		_tag = list(filter(lambda t: t.name == tag, Tag))
		if len(_tag) == 0:
			return routing.HTTP_404({'tag': (04, 'not found')})

		return routing.HTTP_200(_tag[0])

	def html_bytag(self, tag, __callback__, **kwargs):
		ret = __callback__(tag)
		if not isinstance(ret, routing.HTTP_200):
			#TODO: how to reference root app module ?
			#strawberry = sys.modules['strawberry']
			#print strawberry.http401
			#return routing.Redirect(strawberry.http401)
			#	We return an error page:	HTTP code == 404, routed to strawberry.404
			return routing.HTTP_404 #(content=Template('404.html', title='404'))

		tag = ret.msg
		print dir(tag), tag.__fields__
		#TODO: tentacles workaround
		links = list(tag.Link__tags)
		tid   = tag.id
		related = list(filter(lambda t: not t.Link__tags.isdisjoint(links) and t.id	!= tid, Tag))

		from mother.template import Template
		return Template('tag.html',
			title="Tag &#9732; %s" % tag.name,
			query=tag.name,
			tagname=tag.name,
			links=tag.Link__tags,
			searchtags=[],
			related=related,
		)
	"""

