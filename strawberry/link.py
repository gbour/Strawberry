# -*- coding: utf-8 -*-
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
from twisted.web             import server
from mother.callable         import Callable, callback, LoopbackSelf as self
from mother                  import routing

from tentacles               import *
from tentacles.fields        import *
from tentacles.queryset      import filter, len

from tag                     import *


class Link(Object, Callable):
	__stor_name__ = 'strawberry__link'

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


	def __init__(self, *args, **kwargs):
		super(Link, self).__init__(*args, **kwargs)

	def html_GET(self, __callback__, __referer__, **kwargs):
		from mother.template import Template
		from tentacles.queryset import BaseQuerySet

		# call original callback
		values = __callback__(**kwargs)
		values['tags'] = values['tags'].keys()
		print values

		return Template('addoredit.html',
			title='Edit &#9732; '+ str(values['name']),
			tags=list(BaseQuerySet(Tag) >> 'name'),
			values=values,
			mode='edit',
			referer='' if __referer__ == None else __referer__,
			errors={},
		)

	# /!\ GET cannot have a specific content type (global to the object)
	@callback(url='/{id:\d+}', content_type='text/html', modifiers={'text/html': self.html_GET})
	def GET(self, id, __referer__=None):
		link = list(filter(lambda x: x.id == id, Link))
		if len(link) == 0:
			return routing.HTTP_404("%s link not found" % id)

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

		res['tags'] = dict([(t.name, None) for t in link.tags])
		return res

	"""
		TODO: we are actually limited to ONE callback function per url+content_type
				  (method is ignored)
	"""
	@callback(method=('GET','POST'), url='/add', content_type='text/html')
	def html_add(self, __referer__=None, **kwargs):
		if 'tags' in kwargs and not isinstance(kwargs['tags'], list):
			kwargs['tags'] = [kwargs['tags']]

		#TODO: check method == POST
		ret = None
		if 'link' in kwargs:
			ret = self.html_POST(__callback__=self.POST, __referer__=__referer__, **kwargs)
			if isinstance(ret, routing.Redirect):
				return ret

			__referer__ = kwargs.get('referer', None)


		from mother.template import Template
		from tentacles.queryset import BaseQuerySet

		for key in ('link','name'):
			if kwargs.get(key, None) == 'Enter/Paste your url':
				del kwargs[key]

		# remove duplicate values, create list if tags was a single value
		kwargs['tags'] = list(set(kwargs.get('tags',[])))
		for dft in ('', 'nop', 'or enter new one(s)'):
			try:
				kwargs['tags'].remove(dft)
			except:
				pass

		if kwargs.get('description', None) == 'Enter your description here':
			del kwargs['description']

		return Template('addoredit.html',
			title="Add a link",
			tags=list(BaseQuerySet(Tag) >> 'name'),
			values=kwargs,
			mode='add',
			referer='' if __referer__ is None else __referer__,
			errors={} if ret is None else ret.msg,
		)	


	@callback(method='PUT', url='/{id:\d*}')
	def PUT(self, content):
		if 'link' not in content or 'name' not in content:
			return routing.HTTP_400("link, name are mandatory keys")
		
		if 'id' in content and len(filter(lambda x: x.id == content['id'], Link)) > 0:
			return routing.HTTP_400("id already exists")
		if len(filter(lambda x: x.link == content['link'], Link)) > 0:
			return routing.HTTP_400("link must be unique")

		link = Link()
		for key, value in content.iteritems():
			if key == 'tags':
				continue

			if not key in link.__fields__:
				return routing.HTTP_409("unknown field '%s'" % key)
				
			setattr(link, key, value)

		"""We query all tags (by tagname), and create new ones"""
		if 'tags' in content:
			link.tags = list(filter(lambda t: t.name in content['tags'], Tag))
			link.tags.extend([Tag(name=t) for t in content['tags'] if t not in [tag.name for tag in link.tags]])

		link.save()
		return link.id


	def html_POST(self, __callback__, __referer__, **kwargs):
		# cleanup POST args
		if kwargs.get('link', None) == 'Enter/Paste your url':
			del kwargs['link']
		if kwargs.get('name', None) == 'Enter/Paste url name':
			del kwargs['name']

		# remove duplicate values, create list if tags was a single value
		kwargs['tags'] = list(set(kwargs.get('tags',[])))
		for dft in ('', 'nop', 'or enter new one(s)'):
			try:
				kwargs['tags'].remove(dft)
			except:
				pass

		if kwargs.get('description', None) == 'Enter your description here':
			del kwargs['description']

		# generic callback
		ret, link = __callback__(**kwargs)

		"""Handle HTTP routing depending of POST returned values

			4XX: redisplay edit page with error
			200: redirect to referer
		"""
		#if ret.code == routing.HTTP_200:
		if isinstance(ret, routing.HTTP_200):
			import strawberry
			return routing.Redirect(kwargs['referer'] if  len(kwargs.get('referer','')) > 0
					else strawberry)

		# errors: we redisplay the form
		#return url(strawberry.Link, id=values['id']) if 'id' in values else url(strawberry.Link) 
		if 'id' not in kwargs:
			return ret

		# redisplay page
		from mother.template import Template
		from tentacles.queryset import BaseQuerySet
		return Template('addoredit.html',
			title='Edit &#9732; '+link.name,
			tags=list(BaseQuerySet(Tag)),
			values=kwargs,
			mode='edit',
			referer=kwargs.get('referer', ''),
			errors=ret.msg,
		)

	@callback(modifiers={'text/html': self.html_POST})
	def POST(self, *args, **kwargs):
		"""
			if id is set, we edit corresponding link, else we create new one
		"""
		if 'id' in kwargs:
			#link = filter(lambda x: x.id == int(kwargs['id']), Link)
			lid = int(kwargs['id'])
			link = list(filter(lambda x: x.id == lid, Link))

			if len(link) == 0:
				return routing.HTTP_400("'%s' id not found" % kwargs['id'])
			link = link[0]
		else:
			link = Link()

		errors = {}
		# simple fields
		for name, mandatory in {'link': True, 'name': True, 'description': False}.iteritems():
			#NOTE: mandatory fields must be non-null (or empty size)
			#      others can be unset or empty
			if mandatory and (name not in kwargs or len(kwargs[name])) == 0:
				errors[name] = (10, 'field required'); continue
			elif name not in kwargs:
				continue

			try:
				value = link.fieldesc(name).cast(kwargs[name])
			except ValueError:
				errors[name] = (11, 'invalid type'); continue

			setattr(link, name, value)

		# test link is unique
		#TODO: must be done at ORM level (with save() method)

		_link = link.link
		if 'name' not in errors and not link.saved() and\
				len(filter(lambda x: x.link == _link, Link)) > 0:
			errors['link'] = (13, 'not unique')

		# relational field: tags. we get tag names as input...
		tagnames = kwargs['tags'] # tentacles workaroung
		if len(tagnames) == 0:
			errors['tags'] = (12, 'at least one value required')
		else:
			tags     = list(filter(lambda t: t.name in tagnames, Tag))
			newtags  = [Tag(name=name) for name in tagnames if name not in [t.name for t in tags]]

			for t in link.tags:
				tags.remove(t) if t in tags else link.tags.remove(t)

			for t in set(tags).union(newtags):
				link.tags.append(t)


		if len(errors) > 0:
			return routing.HTTP_409(errors), link

		link.save()
		return routing.HTTP_200(link.id), link

	def DELETE(self, id):
		"""
		
			NOTE: associated tags, even if specially created for this link, are not deleted
		"""
		links = list(filter(lambda x: x.id == id, Link))
		if len(links) == 0:
			return routing.HTTP_404("not found")
		elif len(links) > 1:
			return routing.HTTP_500("return several links for the same id")

		links[0].delete()
		return routing.HTTP_200()

	@callback(url='/icon', method=['GET', 'PUT', 'DELETE'])
	def _icon(self, request, id, content=None):
		return self._binary('icon', request, id, content)

	@callback(url='/screenshot', method=['GET', 'PUT', 'DELETE'])
	def _screenshot(self, request, id, content=None):
		return self._binary('screenshot', request, id, content)

	def _binary(self, field, request, id, content):
		link = list(filter(lambda x: x.id == id, Link))
		if len(link) == 0:
			return routing.HTTP_404()
		link = link[0]

		if request.method == 'PUT':
			setattr(link, field, content.read())
			link.save()

			return None

		elif request.method == 'DELETE':
			setattr(link, field, None)
			link.save()
			return None

		# GET
		data = getattr(link, field)
		if data is None:
			return routing.HTTP_204()

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
		res = map(lambda l: {'id': l.id, 'name': l.name}, Link)
		return list(res)

	@callback
	def count(self):
		return str(len(Link))

	@callback
	def bytag(self, tagname):
		#short query form is not available for now
		#res = list(filter(lambda x: tagname in [name for tag in x.tags], Link))
		tags = list(filter(lambda l: l.name == tagname, Tag))
		if len(tags) == 0:
			return routing.HTTP_404()

		tag0 = tags[0]
		return list(map(lambda l: l.id, filter(lambda l: tag0 in l.tags, Link)))

	"""
	class web:
		@callback
		def add(self):
			return 'add a link'

		def post(self):
			return 'post add'
	"""
