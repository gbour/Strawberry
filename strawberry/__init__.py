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
UUID = '554495b2-497a-4835-8786-a6b870815313'

from mother.template import Static, Template
from mother.routing  import ROOT, HTTP_404, HTTP_401, HTTP_403, LOGIN, LOGOUT

from tentacles.queryset import filter, BaseQuerySet
from tag             import *
from link            import *
from strawberry      import *

from mobile          import Mobile

AUTHENTICATION = False
# __name__ is current module name

@callback(content_type='text/html')
def root(**kwargs):
	from mother import routing

	#NOTE: tags list is queried from database
	#      we return queryset, real query is executed at template rendering
	return Template('index.html',	title='All tags',	
			tags=BaseQuerySet(tag.Tag) >> 'name')


@callback(content_type='text/html', url='/tag/{q}')
def search(q, **kwargs):
	"""

		search format:
			a+b-c+"d e"-"f+g"
			give tags: +a, +b, -c, +d e, -f g


		NOTES: 
			. in url encoding, '+' == space and '& %2B == '+'
			  we accept both as plus sign (+ is visually better)

	"""
	# parse querystring
	print 'search=', q

	"""
	import shlex
	def sign(tag):
		if tag[0] in ('+', '-'):
			return (tag[0], tag[1:].decode('utf8'))
		return ('+', tag.decode('utf8'))
	tags = [sign(tag) for tag in shlex.split(q)]
	"""
	import re
	tags = [(s if s == '-' else '+', t.strip('"')) for (s, t) in re.findall("(^|[ +-])([^\" +-]+|\"[^\"]+\")", q)]

	plus  = map(lambda t: t[1], filter(lambda t: t[0] == '+', tags))
	minus = map(lambda t: t[1], filter(lambda t: t[0] == '-', tags))

	plus  = list(filter(lambda t: t.name in plus, Tag))
	minus = list(filter(lambda t: t.name in minus, Tag))

	links = list(filter(lambda l: l.tags.issuperset(plus) and l.tags.isdisjoint(minus), Link))

	#TODO: howto made it simple/clearer ?
	def rset(tag, sign):
		setattr(tag, 'sign', sign); return tag
	tags = map(lambda t: rset(t, '+'), plus)
	tags.extend(map(lambda t: rset(t, '-'), minus))
	tags.sort(key=lambda t: t.name)

	related = list(filter(lambda t: not t.Link__tags.isdisjoint(links) and t not in	plus, Tag))

	return Template('tag.html',
		title="Tag &#9732; "+q,
		#query=q,
		tagname=q,
		links=links,
		tags=tags,
		related=related
	)


URLS = {
	ROOT                 : root,
	HTTP_404             : Template('404.html', title='404'),

	#TODO: accept notation with or without heading '/'
	'/style'             : Static('templates/styles/default', name='style'),
}


