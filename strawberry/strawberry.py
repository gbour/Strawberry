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
import sqlite3, cgi
from mother.callable import callback

class Strawberry(object):
    def __init__(self, db=None):
        self.db     = db
        self.cursor = db.cursor()
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS delicious__link (
                id          INTEGER PRIMARY KEY,
                link        TEXT UNIQUE NOT NULL,
                name        TEXT DEFAULT NULL,
                description TEXT DEFAULT NULL,
                stars       INTEGER DEFAULT 0,
                valid       INTEGER DEFAULT 0,
                creation    TEXT,
                last_change TEXT,
                last_check  TEXT,
                icon        BLOB DEFAULT NULL,
                screenshot  BLOB DEFAULT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS delicious__tag (
                id          INTEGER PRIMARY KEY,
                tag         TEXT UNIQUE,
                description TEXT
            ); 
        """)
    
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS delicious__tag_link (
                tag_id      INTEGER NOT NULL REFERENCES delicious__tag(id),
                link_id     INTEGER NOT NULL REFERENCES delicious__link(id),
                
                PRIMARY KEY (tag_id, link_id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS delicious__tag_tag (
                parent_id   INTEGER NOT NULL REFERENCES delicious__tag(id),
                child_id    INTEGER NOT NULL REFERENCES delicious__tag(id),
                
                PRIMARY KEY (parent_id, child_id)
            )
        """);
        self.db.commit()
        
        # sample data
        try:
            self.cursor.execute("""
                INSERT INTO delicious__link VALUES (
                    1, 
                    'http://devel.bour.cc/strawberry',
                    'strawberry project home page',
                    NULL,
                    5,
                    1,
                    datetime('now'),
                    datetime('now'),
                    datetime('now', '-1 year'),
                    NULL,
                    NULL
                );
            """)
        
            self.cursor.execute("""
                INSERT INTO delicious__tag VALUES (1, "bookmarks service", NULL);
            """)
        
            self.cursor.execute(""" INSERT INTO delicious__tag_link VALUES (1, 1); """)
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.commit()
        
    @callback
    def tags(self, *args, **kwargs):
        """
            return list of tags with number of links related to
        """
        self.cursor.execute("""
            SELECT tag, description, count(*)
                FROM delicious__tag, delicious__tag_link
                WHERE id = tag_id 
                GROUP BY id
                ORDER BY tag
        """)

        ret = []
        for (tag, desc, count) in self.cursor.fetchall():
            ret.append({'tag': tag, 'description': desc, 'count': count})

        return ret


