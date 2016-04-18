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

import os, sys, time
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbeprotocol.protocol import Proxy

logger = getLogger('pellMon')

class nbecomplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)
        self.itemrefs = []
        self.menutags = []
        self.conf = conf
        try:
            self.password = self.conf['password']
        except:
            self.password = '-'
        try:
            self.serial = self.conf['serial']
        except:
            self.serial = None

        item = Getsetitem('controller_online', None, getter=lambda i:1 if self.proxy.controller_online else 0)
        item.tags = ['All','Basic','advanced_data']
        item.type = 'R'
        item.longname = 'Controller online'
        item.description = 'Controller communication status'
        self.itemrefs.append(item)
        self.db.insert(item)
        self.menutags.append('advanced_data')

        item = Getsetitem('controller_IP', None, getter=lambda i:self.proxy.addr[0] if self.proxy.controller_online else '')
        item.tags = ['All','Basic','advanced_data']
        item.type = 'R'
        item.longname = 'Controller IP'
        item.description = 'Controller IP address'
        self.itemrefs.append(item)
        self.db.insert(item)

        self.startthread = threading.Thread(target=lambda:self.start())
        self.startthread.setDaemon(True)
        self.startthread.start()


    def start(self):
        self.proxy = Proxy.discover(self.password, 8483, version='3', serial = self.serial)
        while not self.proxy.controller_online:
            time.sleep(1)
        logger.info('Controller %s found at ip %s'%(self.serial, self.proxy.addr[0]))
        while True:
            try:
                dirlist = self.proxy.dir()
                break
            except Exception as e:
                time.sleep(1)
        def get_value(name):
            item = self.db[name]
            pdata = item.protocoldata
            return  self.proxy.get(int(pdata['function']), pdata['path'])

        def set_value(name, value):
            item = self.db[name]
            pdata = item.protocoldata
            return self.proxy.set(pdata['path'], value)

        def get_group(name):
            if not self.proxy.controller_online:
                raise protocol_offline
            try:
                item = self.db[name]
                pdata = item.protocoldata
                items = self.proxy.get(int(pdata['function']), pdata['grouppath'], group=True)
                for i in items:
                    path, value = i.split('=')
                    name = os.path.basename(path)
                    p = os.path.basename(os.path.dirname(path))
                    n = '-'.join((pdata['group'], name))
                    i = self.db[n]
                    i.update_cache(value)
                return item.cached_value
            except Exception as e:
                print repr(e), 'exc in getgroup', name, time.time()
                raise

        for i in dirlist:
            i_id = i['group'] + '-' + i['name']
            if 'grouppath' in i:
                item = Cacheditem(i_id, i['value'], getter=get_group, setter=set_value, timeout=2)
            else:
                item = Cacheditem(i_id, i['value'], getter=get_value, setter=lambda i,v:self.proxy.set(self.db[i].path, v), timeout=2)
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
