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
import ctypes, os

logger = getLogger('pellMon')

CLOCK_MONOTONIC_RAW = 4 # see <linux/time.h>

class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]

librt = ctypes.CDLL('librt.so.1', use_errno=True)
clock_gettime = librt.clock_gettime
clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

def monotonic_time():
    t = timespec()
    if clock_gettime(CLOCK_MONOTONIC_RAW , ctypes.pointer(t)) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerror(errno_))
    return t.tv_sec + t.tv_nsec * 1e-9

class owmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        self.storeditems = {}
        self.itemvalues = {}
        self.feeder_time = 0
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

        i = Storeditem('feeder_capacity', '1500')
        additem(i, 'R/W')
        i = Getsetitem('feeder_time', '0', getter=lambda item:str(int(self.feeder_time)))
        additem(i, 'R')


        self.update_interval = 0.1

        t = Timer(0, self.update_thread)
        t.setDaemon(True)
        t.start()

    def update_thread(self):
        last_update = None
        self.feeder_time = 0
        while True:
            sleep(self.update_interval)
            try:
                response = requests.get(self.url)#, timeout=5)
                now = monotonic_time()
                if last_update:
                    time_diff = now - last_update
                    feeder_capacity = float(self.db['feeder_capacity'].value) / 360
                    power = float(self.itemvalues['RATED_POWER'])/10
                    proc_id = self.itemvalues['PROC_ID']
                    if proc_id == '5':
                        self.feeder_time +=  (power / 4.8 / 3600) * 1000 * time_diff / feeder_capacity
                    print 'feeder_time:', self.feeder_time, 'timediff:', time_diff, 'power:', power, 'feeder_capacity', feeder_capacity
                last_update = now
                
                root = et.fromstring(response.text)
                for element in root:
                    try:
                        self.itemvalues[element.tag] = unicode(element.text)
                    except KeyError:
                        pass

            except Exception as e:
                print e
                logger.info('MGM update error')
                if self.update_interval < 30:
                    self.update_interval = self.update_interval * 2
            else:
                self.update_interval = 5

