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
from ConfigParser import ConfigParser
from os import path
import traceback
import sys
from threading import Thread, Timer
from time import time, sleep
from logging import getLogger

logger = getLogger('pellMon')

# This is needed to find the local module ownet_fix
sys.path.append(path.dirname(path.abspath(__file__)))
import ownet_fix as ownet

itemList=[]
itemTags={}
Menutags = ['OWFS']

class owfsplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.ow2index={}
        self.name2index={}
        self.sensors={}
        self.latches={}
        self.counters=[]

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
                itemTags[value] = ['All', 'OWFS', 'Basic']
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

                itempath = path.dirname(owpath)
                itemattribute = path.basename(owpath)
                self.sensors[self.ow2index[ow_name]] = ownet.Sensor(itempath, server, port)
                itemList[self.ow2index[ow_name]]['owname'] = itemattribute

            if ow_data == 'type' and value == 'COUNTER':
                itemList[self.ow2index[ow_name]]['function'] = 'COUNTER'
                itemList[self.ow2index[ow_name]]['value'] = 0
                itemList[self.ow2index[ow_name]]['last_i'] = 0
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
                itempath = path.dirname(owpath)
                itemattribute = path.basename(owpath)
                self.latches[self.ow2index[ow_name]] = ownet.Sensor(itempath, server, port)
                itemList[self.ow2index[ow_name]]['owlatch'] = itemattribute

            if ow_data == 'type' and value in ['R','R/W']:
                itemList[self.ow2index[ow_name]]['type'] = value

            t = Timer(0.1, self.background_polling_thread)
            t.setDaemon(True)
            t.start()


    def getItem(self, itemName, poll=False):
        item = itemList[self.name2index[itemName]]
        if poll:
            try:
                if item['function'] == 'COUNTER':
                    return str(item['value'])
                else:
                    sensor = self.sensors[self.name2index[itemName]]
                    name = itemList[self.name2index[itemName]]['owname']
                    name = name.replace('.','_')
                    attr =  getattr(sensor, name)
                    while attr == None:
                        attr =  getattr(sensor, name)
                    item['value'] = str(attr)
                    return str(attr)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
                return str(e)
        else:
            if 'value' in item:
                return item['value']
            else:
                for wait in range(1,15):
                    print 'waiting'
                    sleep(1)
                    if 'value' in item:
                        return item['value']
                return 'error'

    def setItem(self, itemName, value):
        try:
            index = self.name2index[itemName]
            if itemList[index]['type'] == 'R/W':
                sensor = self.sensors[self.name2index[itemName]]
                name = itemList[self.name2index[itemName]]['owname']
                name = name.replace('.','_')
                setattr(sensor, name, value)
                return 'OK'
            else:
                return 'error'
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
            return str(e)

    def counter_thread(self, counter):
        while True:
            try:
                item = itemList[counter]
                l = 0
                if self.latches.has_key(counter):
                    sensor = self.latches[counter]
                    lname = item['owlatch'].replace('.','_')
                    attr =  getattr(sensor, lname)
                    while attr == None:
                        attr =  getattr(sensor, lname)
                    setattr(sensor, lname, 0)
                    l = attr

                if l == 1:
                    sensor = self.sensors[counter]
                    iname = item['owname'].replace('.','_')
                    attr =  getattr(sensor, iname)
                    while attr == None:
                        attr =  getattr(sensor, iname)
                    i = attr

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
                pass
            time.sleep(5)
        
    def background_polling_thread(self):
        while True:
            try:
                for item in itemList:
                    self.getItem(item['name'], poll=True)
            except:
                pass
            sleep(5)

    def getDataBase(self):
        l=[]
        for item in itemList:
            l.append(item['name'])
        return l

    def GetFullDB(self, tags):

        def match(requiredtags, existingtags):
            for rt in requiredtags:
                if rt != '' and not rt in existingtags:
                    return False
            return True
            
        items = [item for item in itemList if match(tags, itemTags[item['name']]) ]
        items.sort(key = lambda k:k['name'])
        return items
        
    def getMenutags(self):
        return Menutags

