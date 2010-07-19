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
import sqlite3
from twisted.web            import server
from mother.callable import Callable, callback


class Link(Callable):
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor()
        
    def GET(self, id):
        self.cursor.execute("""
            SELECT id, link, name, description, stars, valid, creation, last_change, last_check
                FROM delicious__link
                WHERE id = ?
        """, (id,))
        res = self.cursor.fetchone()
        if not res:
            return (404, None)
            
        res = {
            'id'                : res[0],
            'link'              : res[1],
            'name'              : res[2],
            'description'       : res[3],
            'stars'             : res[4],
            'valid'             : res[5],
            'creation'          : res[6],
            'last_change'       : res[7],
            'last_check'        : res[8],
            'tags'              : [],
        }
        
        self.cursor.execute("""
            SELECT id, tag FROM delicious__tag_link, delicious__tag 
                WHERE link_id = ? AND tag_id = id
        """, (res['id'],))
        
        for (id, name) in self.cursor.fetchall():
            res['tags'].append({'id': id, 'tag': name})
            
        return res

        
    def PUT(self, content):
        if 'link' not in content or 'name' not in content:
            return (400, "link, name are required keys")
        
        fields = ['link', 'name', 'description', 'stars', 'valid', 'creation', 
            'last_change', 'last_check']
        f   = []
        v   = []

        for key in content.iterkeys():
            # other are ignored
            if key in fields:
                f.append(key); v.append("'%s'" % content[key])

        r = "INSERT INTO delicious__link (%s) VALUES (%s)" % (', '.join(f), ', '.join(v))
        print r
        try:
            self.cursor.execute(r)
            self.cursor.execute('SELECT last_insert_rowid()')
            linkid = self.cursor.fetchone()[0]
        except sqlite3.IntegrityError:
            return (409, "duplicate link")

        if content.has_key('tags'):
            inttags = []
            strtags = filter(lambda x: isinstance(x, str) or isinstance(x, unicode), content['tags'])

            if len(strtags) > 0:
                r = "SELECT tag, id FROM delicious__tag WHERE tag IN (%s)" % \
                    ', '.join(["'%s'" % t for t in strtags])
                self.cursor.execute(r)
                for (tag, id) in self.cursor.fetchall():
                    inttags.append(id)
                    strtags.remove(tag)

            if len(strtags) > 0:
                r = "INSERT INTO delicious__tag VALUES(NULL, ?, NULL)"
                for tag in strtags:
                    print repr(tag)
                    self.cursor.execute(r, (tag,))
                    inttags.append(self.cursor.lastrowid)

            inttags.extend(filter(lambda x: isinstance(x, int), content['tags']))
            r = "INSERT INTO delicious__tag_link VALUES(?, ?)"
            for tagid in inttags:
                self.cursor.execute(r, (tagid, linkid))

        self.db.commit()
        return linkid
        
    def DELETE(self, id):
        r = "DELETE FROM delicious__link WHERE id = ?"
        try:
            self.cursor.execute(r, (id,))
            if self.cursor.rowcount == 0:
                self.db.rollback()
                return (404, None)
        except sqlite3.IntegrityError:
            self.db.rollback()
            return (401, "not found")

        self.db.commit()
        return True

    @callback(method=['GET', 'PUT', 'DELETE'])
    def icon(self, request, id, content=None):
        print "icon:", request.method, id
        return self._binary('icon', request, id, content)

    @callback(method=['GET', 'PUT', 'DELETE'])
    def screenshot(self, request, id, content=None):
        print "screenshot:", request.method, id
        return self._binary('screenshot', request, id, content)

    def _binary(self, field, request, id, content):
        if request.method == 'PUT':
            data = content.read()
            r = "UPDATE delicious__link SET %s = ? WHERE id = ?" % field
            self.cursor.execute(r, (sqlite3.Binary(data), id))
            self.db.commit()

            if self.cursor.rowcount == 1:
                return None
            return (404, None)

        elif request.method == 'DELETE':
            r = "UPDATE delicious__link SET %s = NULL WHERE id = ?" % field
            self.cursor.execute(r, (id,))
            self.db.commit()

            if self.cursor.rowcount == 1:
                return None
            return (404, None)

            
        # GET
        r = "SELECT %s FROM delicious__link WHERE id = ?" % field
        self.cursor.execute(r, (id,))
         
        # sqlite BLOB is mapped to buffer python type
        data = self.cursor.fetchone()[0]
        if data is None:
            return (404, None)
        
        request.setHeader('Content-Type', "image/vnd.microsoft.icon")
        request.write(str(data))
        request.finish()
        
        return server.NOT_DONE_YET

    @callback
    def all(self):
        r = "SELECT id FROM delicious__link"
        return map(lambda x: x[0], self.cursor.execute(r))

        return self.cursor.fetchall()

    @callback
    def bytag(self, tagname):
        r = """SELECT l.id 
            FROM delicious__link as l, delicious__tag as t, delicious__tag_link as tl
            WHERE l.id = tl.link_id AND tl.tag_id = t.id
            AND t.tag = ?
        """
        return map(lambda x: x[0], self.cursor.execute(r, (tagname,)))


