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

# This is needed to find the local module ownet_fix
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
        #self.attributes = {}
        for key, value in self.conf.iteritems():
            port = 4304
            server = 'localhost'
            ow_name = key.split('_')[0]
            ow_data = key.split('_')[1]

            if not self.ow2index.has_key(ow_name):
                itemList.append({'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})
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
                    port = val[1]
                owpath = val[0]

                itempath = path.dirname(owpath)
                itemattribute = path.basename(owpath)
                self.sensors[self.ow2index[ow_name]] = ownet.Sensor(itempath, server, int(port))
                itemList[self.ow2index[ow_name]]['owname'] = itemattribute
            if ow_data == 'type' and value in ['R','R/W','COUNTER']:
                itemList[self.ow2index[ow_name]]['type'] = value

    def getItem(self, itemName):
        try:
            sensor = self.sensors[self.name2index[itemName]]
            name = itemList[self.name2index[itemName]]['owname']
            name = name.replace('.','_')
            attr =  getattr(sensor, name)
            while attr == None:
                attr =  getattr(sensor, name)
            return str(attr)
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
            return str(e)

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

