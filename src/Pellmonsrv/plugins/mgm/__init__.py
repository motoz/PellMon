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
from Pellmonsrv.database import Getsetitem, Storeditem
from logging import getLogger
from threading import Timer
from time import sleep
import xml.etree.ElementTree as et
import requests
logger = getLogger('pellMon')

class owmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        self.storeditems = {}
        self.itemvalues = {}
        try:
            self.url = self.conf['url']
        except:
            logger.info('"url" missing from mgm plugin configuration')
            return

        def additem(i, item_type='R'):
            i.tags = ['All', 'Basic', 'MGM']
            i.type = item_type
            i.min = ''
            i.max = ''
            self.db.insert(i)
            self.itemrefs.append(i)

        config = {}
        for index_key, value in self.conf.items():
            if '_' in index_key:
                index, key = index_key.split('_')
                try:
                    config[index][key] = value
                except KeyError:
                    config[index] = {key:value}

        for index, itemconf in config.items():
            try:
                itemname = itemconf.pop('item')
                itemvalue = itemconf.pop('default', '0')
                itemdata = itemconf.pop('data');

                i = Getsetitem(itemname, itemvalue, getter=lambda item, d=itemdata:self.itemvalues[d])

                for key, value in itemconf.items():
                    setattr(i, key, value)
                additem(i)
                self.itemvalues[i]=itemvalue

            except KeyError:
                pass

        self.update_interval = 1

        t = Timer(0, self.update_thread)
        t.setDaemon(True)
        t.start()

    def update_thread(self):
        while True:
            sleep(self.update_interval)
            try:
                response = requests.get(self.url)
                root = et.fromstring(response.text)
                for element in root:
                    try:
                        self.itemvalues[element.tag] = unicode(element.text)
                    except KeyError:
                        pass
            except Exception as e:
                logger.info('MGM update error')
                if self.update_interval < 600:
                    self.update_interval = self.update_interval * 2
            else:
                self.update_interval = 1

