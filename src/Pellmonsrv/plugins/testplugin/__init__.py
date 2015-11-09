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
from logging import getLogger

logger = getLogger('pellMon')

itemList = [{'name':'testitem1', 'longname':'test item 1', 'type':'W'}, {'name':'testitem2', 'type':'R', 'unit':'m/s'}, {'name':'testitem3', 'type':'R/W',  'min':'0', 'max':'100', 'unit':'HP'}]

itemTags = {'testitem1' :     ['All', 'testplugin', 'Basic'],
            'testitem2' :     ['All', 'testplugin', 'Basic', 'Overview'],
            'testitem3' :     ['All', 'testplugin'],
}

itemDescriptions = {'testitem2' : 'This is test item 2',
}

class testplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        for i in itemList:
            try:
                i['value'] = i['min']
            except:
                i['value'] = '1234'
        for key, value in self.conf.iteritems():
            itemList.append({'name':key, 'value':value, 'min':0, 'max':100, 'unit':'W', 'type':'R/W'})
            itemTags[key] = ['All', 'testplugin', 'Basic']
        logger.info('testplugin activated...')

    def getItem(self, item):
        for i in itemList:
            if i['name'] == item:
                logger.debug('testplugin: Get %s=%s'%(item,i['value']))
                return i['value']

    def setItem(self, item, value):
        for i in itemList:
            if i['name'] == item:
                i['value'] = value
                logger.debug('testplugin: Set %s=%s'%(item,str(value)))
                return 'OK'
        return['error']

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
        for item in items:
            try:
                item['description'] = itemDescriptions[item['name']]
            except:
                item['description'] = ''
        return items

    def getMenutags(self):
        return ['testplugin', 'Overview']
