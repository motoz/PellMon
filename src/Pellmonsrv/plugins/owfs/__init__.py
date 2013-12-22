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
import ownet

itemList=[]
itemTags={}
Menutags = ['OWFS']

class owfsplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)

        self.sensors = {}
        self.attributes = {}
        for key, value in self.conf.iteritems():
            itempath = path.dirname(value)
            itemattribute = path.basename(value)
            itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})           
            itemTags[key] = ['All', 'OWFS', 'Basic']
            self.sensors[key] = ownet.Sensor(itempath, 'localhost', 4304)
            self.attributes[key] = itemattribute

    def getItem(self, itemName):
        try:
            return self.sensors[itemName].temperature
        except AttributeError:
            try:
                s = self.sensors[itemName]
                attr = s._connection.read(object.__getattribute__(s, '_attrs')[self.attributes[itemName]])
                return str(attr)
            except:
                return 'error'

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

