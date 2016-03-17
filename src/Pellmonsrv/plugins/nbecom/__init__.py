#! /usr/bin/python
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

from Pellmonsrv.plugin_categories import protocols
from Pellmonsrv.database import Item, Getsetitem, Storeditem, Cacheditem
from logging import getLogger

import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbeprotocol.protocol import Proxy

logger = getLogger('pellMon')

class nbecomplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def dir_recursive(self, path='*'):
        out = []
        pathlist = self.proxy.get(path)
        for path in pathlist:
            if path[-1] == '/':
                try:
                    out += self.dir_recursive(path)
                except IOError:
                    print 'error:', path
            else:
                out.append(path)
        return out

    
    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)
        self.itemrefs = []
        self.menutags = []
        self.conf = conf
        try:
            self.password = self.conf['password']
        except:
            self.password = '-'
        self.proxy = Proxy.discover(self.password, 1900, version='3')

        def additems(items, group, itemtype, itemtag=None):
            for i in items:
                i = i.encode('ascii')
                fullpath = i
                value = ''
                try:
                    fullpath, value = fullpath.split('=',1)
                except:
                    pass
                if itemtag is None:
                    tag = os.path.dirname(os.path.relpath(fullpath, group))
                    name = os.path.basename(fullpath)
                    id = '-'.join((tag, name))
                    #print tag, name
                else:
                    name = os.path.relpath(fullpath, group)
                    tag = itemtag
                    id = '-'.join((tag, name))

                def get_group(name):
                    item = self.db[name]
                    try:
                        items = self.proxy.get(item.grouppath)
                    except Exception as e:
                        raise
                    try:
                        for i in items:
                            path, value = i.split('=')
                            name = os.path.basename(path)
                            p = os.path.basename(os.path.dirname(path))
                            n = '-'.join((p,name))
                            i = self.db[n]
                            i.update_cache(value)
                        return item.cached_value
                    except Exception as e:
                        print 'err', e, i
                        return 'error'

                def get_value(name):
                    item = self.db[name]
                    value = self.proxy.get(item.path)[0]
                    value = value.split('=')[1]
                    return value

                if '=' in i:
                    item = Cacheditem(id, value, getter=get_group, setter=lambda i,v:self.proxy.set(self.db[i].path, v), timeout=1)
                else:
                    item = Cacheditem(id, value, getter=get_value, setter=lambda i,v:self.proxy.set(self.db[i].path, v), timeout=10)
                item.path =  i.split('=',1)[0]
                item.longname = name
                
                item.grouppath = os.path.dirname(item.path)
                item.type = itemtype

                if tag not in self.menutags:
                    self.menutags.append(tag)
                item.tags = ['All', 'Basic']
                item.tags.append(tag)

                self.itemrefs.append(item)
                self.db.insert(item)
                item = Cacheditem('sw_versions', None, getter=lambda i:' /   '.join(self.proxy.get('sw_versions')), timeout=10)
                item.type = 'R'
                item.tags = ['All', 'Basic', 'sw_versions']
                self.menutags.append('sw_versions')
                self.itemrefs.append(item)
                self.db.insert(item)
                
        items = self.dir_recursive('settings/')
        additems(items, 'settings', 'R/W')
        items = self.dir_recursive('operating_data/')
        additems(items, 'operating_data', 'R', 'operating_data')
        items = self.dir_recursive('advanced_data/')
        additems(items, 'advanced_data', 'R', 'advanced_data')
        items = self.dir_recursive('consumption_data/')
        additems(items, 'consumption_data', 'R', 'consumption_data')
        
    def getMenutags(self):
        return self.menutags
