#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from weakref import WeakValueDictionary
import time
import sqlite3, threading

class Keyval_storage:
    keyval_storage = None

def init_keyval_storage(f):
    Keyval_storage.keyval_storage = Keyval_storage(f)

class Item(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value

class Getsetitem(Item):
    def __init__(self, name, getter, setter, value=None):
        self.getter = getter
        self.setter_use_later = setter
        def first_set(*args, **kwargs):
            # Don't call the setter on the first property set, that's from init
            self.setter = self.setter_use_later
        self.setter = first_set 
        super(Getsetitem, self).__init__(name, value)
        self._value = value

    @property
    def value(self):
        if self.getter is not None:
            self._value = self.getter(self.name)
        return self._value

    @value.setter
    def value(self, value):
        if self.setter is not None:
            self.setter(self.name, value)
        self._value = value

class Cacheditem(Getsetitem):
    def __init__(self, name, getter, setter, value=None):
        self.update_time = 0
        super(Cacheditem, self).__init__(name, getter, setter, value)

    @Getsetitem.value.getter
    def value(self):
        if time.time() - self.update_time < 5:
            return self.cached_value
        else:
            self.cached_value = self.getter(self.name)
            self.update_time = time.time()
            return self.cached_value

class Storeditem(Getsetitem):
    def __init__(self, name, value=None, getter=None, setter=None):
        self.update_time = 0
        self._value = value
        super(Storeditem, self).__init__(name, getter, setter, value)
        Keyval_storage.keyval_storage.writeval(self.name, confval=value)
        self._value = Keyval_storage.keyval_storage.readval(self.name)

    @Getsetitem.value.setter
    def value(self, value):
     try:
        Getsetitem.value.setter(self)
        if value != self._value:
            self.setter(self.name, value)
            Keyval_storage.keyval_storage.writeval(self.name, value)
            self._value = value
     except Exception, e:
        print e
        raise

class Database(WeakValueDictionary):
    def __init__(self):
        WeakValueDictionary.__init__(self)
    
    def insert(self, item):
        self[item.name] = item

    def get_item(self, name):
        return self[name]

    def get_value(self, name):
        return self[name].value

    def set_value(self, name, value):
        try:
            self[name].value = value
            return 'OK'
        except Exception, e:
            return 'error'

class Keyval_storage(object):
    def __init__(self, dbfile):
        self.dbfile = dbfile
        conn = sqlite3.connect(dbfile)
        cursor = conn.cursor()
        self.lock = threading.Lock()
        try:
            cursor.execute("SELECT value from keyval")
        except sqlite3.OperationalError:
            cursor.execute("CREATE TABLE keyval (id TEXT PRIMARY KEY, value TEXT, confvalue TEXT NOT NULL DEFAULT '-')")
        conn.commit()
        conn.close()

    def readval(self, item):
        with self.lock:
            try:
                conn = sqlite3.connect(self.dbfile)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM keyval WHERE id=?", (item,))
                value, = cursor.next()
                conn.close()
                return value
            except Exception, e:
                print e
                return 'error'

    def writeval(self, item, value=None, confval=None):
        value = unicode(value)
        with self.lock:
            try:
                conn = sqlite3.connect(self.dbfile)
                cursor = conn.cursor()
                if confval is None:
                    cursor.execute("""INSERT OR REPLACE INTO keyval (id, value, confvalue   ) VALUES (
                                            ?,?,(select confvalue from keyval where id =    ?
                                    ))""", (item, value, item))
                    conn.commit()
                else:
                    try:
                        cursor.execute("SELECT value, confvalue FROM keyval WHERE id=?", (item,))
                        value,confvalue = cursor.next()
                        if confvalue != confval:
                            cursor.execute("INSERT OR REPLACE INTO keyval (id, value, confvalue) VALUES (?,?,?)", (item, confval, confval))
                            conn.commit()
                    except:
                        cursor.execute("INSERT OR REPLACE INTO keyval (id, value, confvalue) VALUES (?,?,?)", (item, confval, confval))
                        conn.commit()
                conn.close()
            except Exception as e:
                     e
                raise
