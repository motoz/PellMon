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
        self.proxy = Proxy.discover(self.password, 8483, version='3')

        dirlist = self.proxy.dir()

        def get_group(name):
            try:
              with self.proxy.lock:
                item = self.db[name]
                pdata = item.protocoldata
                items = self.proxy.make_request(int(pdata['function']), pdata['grouppath']).payload
                if pdata['group'] == 'operating_data':
                    pass #print items
                items = items.encode('ascii').split(';')
            except Exception as e:
                print e, 'exc'
                import traceback
                traceback.print_exc()
                raise
            try:
                for i in items:
                    path, value = i.split('=')
                    name = os.path.basename(path)
                    p = os.path.basename(os.path.dirname(path))
                    n = '-'.join((pdata['group'], name))
                    i = self.db[n]
                    i.update_cache(value)
                return item.cached_value
            except Exception as e:
                print 'err', e, i
                import traceback
                traceback.print_exc()
                return 'error'

        def get_value(name):
            item = self.db[name]
            pdata = item.protocoldata
            try:
                with self.proxy.lock:
                    value = self.proxy.make_request(int(pdata['function']), pdata['path']).payload
            except:
                value = 'error'
            value = value.split('=', 1)[1]
            return value

        def set_value(name, value):
            item = self.db[name]
            pdata = item.protocoldata
            try:
                r = self.proxy.make_request(2, pdata['path']+'='+value, encrypt=True)
                return r
            except:
                return 'error'

        for i in dirlist:
            i_id = i['group'] + '-' + i['name']
            if 'grouppath' in i:
                item = Cacheditem(i_id, i['value'], getter=get_group, setter=set_value, timeout=1)
            else:
                item = Cacheditem(i_id, i['value'], getter=get_value, setter=lambda i,v:self.proxy.set(self.db[i].path, v), timeout=10)
            item.protocoldata =  i
            item.longname = i['name']
            item.type = i['type']
            try:
                item.min = i['min']
                item.max = i['max']
            except KeyError:
               pass
            if i['group'] not in self.menutags:
                self.menutags.append(i['group'])
            item.tags = ['All', 'Basic', i['group']]
            #item.tags.append(tag)

            self.itemrefs.append(item)
            self.db.insert(item)

        item = Getsetitem('feeder_capacity', None, getter=lambda i:self.db['auger-auger_capacity'].value)
        self.itemrefs.append(item)
        self.db.insert(item)
        self.feeder_time = 0
        self.counter = None
        def get_feeder_time(i):
            ac = float(self.db['auger-auger_capacity'].value)
            counter = float(self.db['consumption_data-counter'].value)
            counterdiff = 0 if self.counter is None else counter - self.counter
            self.counter = counter
            self.feeder_time += counterdiff * 1000 / ac * 360
            return str(int(self.feeder_time))    

        item = Getsetitem('feeder_time', None, getter=get_feeder_time)
        self.itemrefs.append(item)
        self.db.insert(item)


    def getMenutags(self):
        return self.menutags
