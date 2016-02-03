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

class Item(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value

class Getsetitem(Item):
    def __init__(self, name, getter, setter):
        self.getter = getter
        self.setter = setter
        super(Getsetitem, self).__init__(name, None)

    @property
    def value(self):
        v = self.getter(self.name)
        return v

    @value.setter
    def value(self, value):
        self.setter(self.name, value)

class Cacheditem(Getsetitem):
    def __init__(self, name, getter, setter):
        self.update_time = 0
        super(Cacheditem, self).__init__(name, getter, setter)

    @Getsetitem.value.getter
    def value(self):
        if time.time() - self.update_time < 5:
            return self.cached_value
        else:
            self.cached_value = self.getter(self.name)
            self.update_time = time.time()
            return self.cached_value

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
        except:
            return 'error'

