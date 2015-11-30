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
import traceback
from threading import Thread, Timer
from time import time, sleep
from logging import getLogger
import re

logger = getLogger('pellMon')

class onewireplugin(protocols):
    def __init__(self):
        protocols.__init__(self)
        self.itemList=[]
        self.items = {}
        self.itemTags={}
        self.Menutags = ['Onewire']
        self.w1_therm_temperature = re.compile(r't=([0-9]+)')

    def activate(self, conf, glob):
        """ Create the items described in the configuration file and activate the plugin """
        protocols.activate(self, conf, glob)
        try:
            itemconfigs = {}

            # Group item configuration values according to the part before '_' in the key
            for key, value in conf.iteritems():
                lvalue, itemconfig = key.split('_')

                # Use 'item' for the item name in the configuration file as usual
                if itemconfig == 'item':
                    itemconfig = 'name'

                if lvalue not in itemconfigs:
                    itemconfigs[lvalue] = {}
                itemconfigs[lvalue][itemconfig] = value

            # Add the configuration values to itemList
            for lvalue, itemconfig in itemconfigs.items():
                # First add the defaults
                item = {'min':'', 'max':'', 'unit':'', 'type':'R', 'description':'', 'family':'w1_therm'}
                # Then update with the data from the configuration file
                item.update(itemconfig)
                # And add the item to the list
                self.itemList.append(item)
                # Put the item in the items dictionary also where it's accessible by name
                name = item['name']
                self.items[name] = item
                # And give it some default tags so it's visibla in the web interface
                self.itemTags[name] = ['Basic', 'All', 'Onewire']

            t = Timer(0.1, self.background_polling_thread)
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.debug('Onewire activate failed: %s'%str(e))
            print e

    def getItem(self, itemName, background_poll=False):
        """ Return the cached item value, or return a frech value when background_poll=True """
        item = self.items[itemName]
        if item['family'] == 'w1_therm':
            if background_poll:
                try:
                    with open(item['path'], 'r') as f:
                        l1 = f.readline()
                        l2 = f.readline()
                    if l1.rstrip()[-3:] == 'YES':
                        match = self.w1_therm_temperature.search(l2)
                        if match:
                            return str(float(match.group(1)) / 1000)
                    return 'error'
                except Exception, e:
                    return 'error'
            else:
                if 'value' in item:
                    return item['value']
                else:
                    for wait in range(15):
                        sleep(1)
                        if 'value' in item:
                            return item['value']
                    return 'error'
        else:
            return 'error'

    def setItem(self, itemName, value):
        return 'error'

    def background_polling_thread(self):
       """ Update the item values every five seconds """
       while True:
            try:
                for item in self.itemList:
                    item['value'] = self.getItem(item['name'], background_poll=True)
            except Exception, e:
                logger.debug('onewire background poll error: '+str(e))
            sleep(5)

    def getDataBase(self):
        """ Return a list of the item names added by this plugin """
        return [item['name'] for item in self.itemList]

    def GetFullDB(self, tags):
        """ Return a list of the items that have matching tags """
        def match(requiredtags, existingtags):
            for rt in requiredtags:
                if rt != '' and not rt in existingtags:
                    return False
            return True
            
        items = [item for item in self.itemList if match(tags, self.itemTags[item['name']]) ]
        items.sort(key = lambda k:k['name'])
        return items

    def getMenutags(self):
        """ Return a list of the menus addded by this plugin """
        return self.Menutags

