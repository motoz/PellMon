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
from Pellmonsrv.database import Item, Getsetitem, Storeditem
from logging import getLogger

logger = getLogger('pellMon')

itemList = [
    {'name':'testitem1', 'value':'0', 'longname':'test button', 'min':'0', 'max':'100', 'type':'W'},
    {'name':'testitem2', 'value':'0', 'type':'R', 'min':'0', 'max':'100', 'unit':'m/s'}, 
    {'name':'testitem3', 'value':'0', 'type':'R/W',  'min':'0', 'max':'100', 'unit':'HP'}]

itemTags = {'testitem1' :     ['All', 'testplugin', 'Basic'],
            'testitem2' :     ['All', 'testplugin', 'Basic', 'Overview'],
            'testitem3' :     ['All', 'testplugin'],
}

itemDescriptions = {'testitem2' : 'This is test item 2',
}

class testplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        self.itemvalues = {}

        for key, value in self.conf.iteritems():
            itemList.append({'name':key, 'value':value, 'min':'0', 'max':'100', 'unit':'km', 'type':'R/W'})
            itemTags[key] = ['All', 'testplugin', 'Basic']

        for item in itemList:
            self.itemvalues[item['name']] = item['value']

            dbitem = Getsetitem(item['name'], item['value'], lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
            for key, value in item.iteritems():
                if key is not 'value':
                    dbitem.__setattr__(key, value)
            if dbitem.name in itemTags:
                dbitem.__setattr__('tags', itemTags[dbitem.name])
            self.db.insert(dbitem)
            self.itemrefs.append(dbitem)
            def mysetter(name, value):
                print 'testplugin set: ', name, value
            i = Storeditem('stored', 'defaultvalue', setter=mysetter)
            i.tags = ['All', 'testplugin', 'Basic'] 
            i.type = 'R/W'
            i.min = '0'
            i.max = '120'
            i.unit = 'm'
            i.description = "this is a test item"
            i.longname = "stored item"
            self.db.insert(i)
            self.itemrefs.append(i)

    def getItem(self, item):
        v = self.itemvalues[item]
        logger.debug('testplugin: Get %s=%s'%(item, v))
        return v

    def setItem(self, item, value):
        self.itemvalues[item] = value
        logger.debug('testplugin: Set %s=%s'%(item,unicode(value)))

