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
from threading import Thread, Timer
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd
from time import time
from datetime import datetime
from logging import getLogger

logger = getLogger('pellMon')

itemList=[{'name':'silo_reset_level',  'longname':'Silo fill up level',
           'type':'R/W',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'50000'},
          {'name':'silo_reset_time',   'longname':'Silo fill up time', 
           'type':'R/W',   'unit':''    ,   'value':'-', 'min':'0', 'max':'-'},
         ]

itemTags = {'silo_reset_level' :    ['All', 'Basic', 'SiloLevel'],
            'silo_reset_time' :     ['All', 'Basic', 'SiloLevel'],
           }

itemDescriptions = {'silo_reset_level':     'Silo fill up to this amount',
                    'silo_reset_time' :     'dd/mm/yy hh:mm Automatically set when setting fill up level',
                   }

itemValues={}
Menutags = ['SiloLevel']

class silolevelplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.valuestore = ConfigParser()
        self.valuestore.add_section('values')
        self.valuesfile = path.join(path.dirname(__file__), 'values.conf')
        for item in itemList:
            if item['type'] == 'R/W':
                self.valuestore.set('values', item['name'], item['value'])
            else:
                itemValues[item['name']] = item['value']
        self.valuestore.read(self.valuesfile)
        f = open(self.valuesfile, 'w')
        self.valuestore.write(f)
        f.close()
        try:
            uid = pwd.getpwnam(self.glob['conf'].USER).pw_uid
            gid = grp.getgrnam(self.glob['conf'].GROUP).gr_gid
            os.chown(self.valuesfile, uid, gid)
        except:
            pass

    def getItem(self, itemName):
        for i in itemList:
            if i['name'] == itemName:
                return str(self.valuestore.get('values', itemName))
        return 'error'

    def setItem(self, item, value):
        try:
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                self.valuestore.set('values', item, str(value))
                f = open(self.valuesfile, 'w')
                self.valuestore.write(f)
                f.close()
                if item=='silo_reset_level':
                    d = datetime.fromtimestamp(time())
                    s = d.strftime('%d/%m/%y %H:%M')
                    self.setItem('silo_reset_time', s)
                return 'OK'
        except Exception,e:
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
        for item in items:
            item['description'] = itemDescriptions[item['name']]
        return items
        
    def getMenutags(self):
        return Menutags

