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
from Pellmonsrv.database import Item, Getsetitem
from ConfigParser import ConfigParser
from os import path
import traceback
import sys
from threading import Thread, Timer
from time import time, sleep
from logging import getLogger

logger = getLogger('pellMon')

itemList=[]
itemTags={}
Menutags = ['OWFS']

class owfsplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        try:
            self.protocol = __import__('pyownet.protocol').protocol
        except ImportError:
            logger.info('OWFS: python module pyownet is missing')
            raise
        protocols.activate(self, conf, glob, db)
        self.ow2index={}
        self.name2index={}
        self.sensors={}
        self.latches={}
        self.counters=[]
        self.proxies = {}
        self.itemrefs = []

        for key, value in self.conf.iteritems():
            port = 4304
            server = 'localhost'
            ow_name = key.split('_')[0]
            ow_data = key.split('_')[1]

            if not self.ow2index.has_key(ow_name):
                itemList.append({'min':'', 'max':'', 'unit':'', 'type':'R', 'description':'', 'function':'input'})
                self.ow2index[ow_name] = len(itemList)-1
                
            if ow_data == 'item':
                itemList[self.ow2index[ow_name]]['name'] = value
                self.name2index[value]=self.ow2index[ow_name]

            if ow_data == 'path':
                val = value.split('::')
                if len(val) == 2:
                    server = val[0]
                    val[0] = val[1]
                val = val[0].split(':')
                if len(val) == 2:
                    port = int(val[1])
                owpath = val[0]

                if 'uncached' in owpath:
                    itemList[self.ow2index[ow_name]]['uncached'] = True
                else:
                    itemList[self.ow2index[ow_name]]['uncached'] = False

                self.sensors[self.ow2index[ow_name]] = (owpath, server)
                if not server in self.proxies:
                    try:
                        self.proxies[server] = self.protocol.proxy(host=server, port=port)
                    except self.protocol.ConnError, e:
                        self.proxies[server] = (server, port)
                    
            if ow_data == 'type' and value == 'COUNTER':
                itemList[self.ow2index[ow_name]]['function'] = 'COUNTER'
                itemList[self.ow2index[ow_name]]['value'] = 0
                itemList[self.ow2index[ow_name]]['last_i'] = b'0'
                itemList[self.ow2index[ow_name]]['toggle'] = 0
                t = Timer(5, self.counter_thread, args=(self.ow2index[ow_name],))
                t.setDaemon(True)
                t.start()

            if ow_data == 'latch':
                val = value.split('::')
                if len(val) == 2:
                    server = val[0]
                    val[0] = val[1]
                val = val[0].split(':')
                if len(val) == 2:
                    port = int(val[1])
                owpath = val[0]
                self.latches[self.ow2index[ow_name]] = (owpath, server)
                if not server in self.proxies:
                    try:
                        self.proxies[server] = self.protocol.proxy(host=server, port=port)
                    except self.protocol.ConnError, e:
                        self.proxies[server] = (server, port)

            if ow_data == 'type' and value in ['R','R/W']:
                itemList[self.ow2index[ow_name]]['type'] = value

        # Create dbitems from the list and insert into the database
        for item in itemList:
            dbitem = Getsetitem(item['name'], lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
            for key, value in item.iteritems():
                dbitem.__setattr__(key, value)
            # Give it some default tags so it's visible in the web interface
            dbitem.__setattr__('tags', ['Basic', 'All', 'OWFS'])
            self.db.insert(dbitem)
            self.itemrefs.append(dbitem)


        t = Timer(0.1, self.background_polling_thread)
        t.setDaemon(True)
        t.start()


    def getItem(self, itemName, background_poll=False):
        item = itemList[self.name2index[itemName]]
        if (background_poll and item['uncached'] is False) or (
            item['uncached'] and background_poll is False):
            try:
                if item['function'] == 'COUNTER':
                    return str(item['value'])
                else:
                    path, server = self.sensors[self.name2index[itemName]]
                    try:
                        proxy = self.proxies[server]
                        data = proxy.read(path)
                        item['value'] = data.decode('ascii').strip()
                        return item['value']
                    except AttributeError:
                        host, port = self.proxies[server]
                        proxy = self.protocol.proxy(host=host, port=port)
                        self.proxies[server] = proxy
                        data = proxy.read(path)
                        item['value'] = data.decode('ascii').strip()
                        return item['value']
                        
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print exc_type, exc_value
                traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
                return str(e)
        elif not background_poll:
            if 'value' in item:
                return item['value']
            else:
                for wait in range(1,15):
                    sleep(1)
                    if 'value' in item:
                        return item['value']
                return 'error'

    def setItem(self, itemName, value):
        try:
            index = self.name2index[itemName]
            if itemList[index]['type'] == 'R/W':
                path, server = self.sensors[self.name2index[itemName]]
                proxy = self.proxies[server]

                try:
                    proxy = self.proxies[server]
                    proxy.write(path, str(value))
                    return 'OK'
                except AttributeError:
                    host, port = self.proxies[server]
                    proxy = self.protocol.proxy(host=host, port=port)
                    self.proxies[server] = proxy
                    proxy.write(path, str(value))
                    return 'OK'
            else:
                return 'error'
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print exc_type, exc_value
            traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
            return 'error'

    def counter_thread(self, counter):
        while True:
            try:
                item = itemList[counter]
                l = 0
                if self.latches.has_key(counter):
                    path, server = self.latches[counter]
                    proxy = self.proxies[server]
                    try:
                        proxy = self.proxies[server]
                        data = proxy.read(path)
                    except AttributeError:
                        host, port = self.proxies[server]
                        proxy = self.protocol.proxy(host=host, port=port)
                        self.proxies[server] = proxy
                        data = proxy.read(path)
                        
                    l = int(data)
                    if l:
                        proxy.write(path, b'0')
 
                if (counter in self.latches and l == 1) or (counter not in self.latches):
                    path, server = self.sensors[counter]
                    proxy = self.proxies[server]
                    i = proxy.read(path)
        
                    if i == item['last_i']:
                        item['value'] += 1
                        item['toggle'] = 0
                    else:
                        item['toggle'] += 1
                        if item['toggle'] == 2:
                            item['last_i'] = i
                            item['value'] +=1
                            item['toggle'] = 0
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print exc_type, exc_value
                traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
                logger.debug('OWFS counter error '+str(e))
            sleep(5)
        
    def background_polling_thread(self):
       while True:
            try:
                for item in itemList:
                    self.getItem(item['name'], background_poll=True)
            except Exception, e:
                logger.debug('OWFS background poll error: '+str(e))
            sleep(5)

    def getMenutags(self):
        return Menutags

