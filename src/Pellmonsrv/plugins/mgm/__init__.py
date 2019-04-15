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
from time import sleep, time
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

class mgmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        self.storeditems = {}
        self.itemvalues = {}
        self.feeder_time = 0
        self.errorcounter = 0

        def additem(i, item_type='R'):
            i.tags = ['All', 'Basic', 'MGM']
            i.type = item_type
            i.min = ''
            i.max = ''
            self.db.insert(i)
            self.itemrefs.append(i)

        i = Storeditem('mgm_ip', '0.0.0.0')
        i.label = 'MGM IP'
        i.longname = 'MGM IP'
        i.description = 'The IP that the MGM controller is reachable on'
        additem(i, 'R/W')

        config = {}
        for index_key, value in self.conf.items():
            if '_' in index_key:
                index, key = index_key.rsplit('_', 1)
                try:
                    config[index][key] = value
                except KeyError:
                    config[index] = {key:value}
        # Get all enumerations
        enumerations = {}
        for enum_id, enum in config.items():
            enum_id = enum_id.split('_')
            try:
                if enum_id[1] == 'enum':
                    enumerations[enum_id[0]] = enum
            except IndexError:
                pass

        # Get all item definitions
        for index, itemconf in config.items():
            try:
                itemname = itemconf.pop('item')
                itemvalue = itemconf.pop('default', '0')
                try:
                    itemdata = itemconf.pop('data');
                    try:
                        scalefactor = itemconf.pop('scalefactor', '1')
                        scalefactor = float(scalefactor) 
                    except ValueError:
                        logger.info('MGM plugin: invalid scaling factor %s'%scalefactor)
                    try:
                        bitmask = itemconf.pop('bitmask', None)
                        bitmask = int(scalefactor) 
                    except ValueError:
                        logger.info('MGM plugin: invalid bitmask %s'%bitmask)

                    itemenumeration = itemconf.pop('enumeration', None)
                    if itemenumeration:
                        enum = enumerations[itemenumeration]
                        getfunc = lambda item,d=itemdata,e=enum: e[self.itemvalues[d]]
                    elif scalefactor == 1:
                        getfunc = lambda item,d=itemdata:self.itemvalues[d]
                    elif bitmask:
                        getfunc = lambda item, d=itemdata,s=scalefactor,m=bitmask:str((int(self.itemvalues[d]) & m)*s)
                    else:
                        getfunc = lambda item, d=itemdata,s=scalefactor:str(float(self.itemvalues[d])*s)
                    i = Getsetitem(itemname, itemvalue, getter=getfunc)

                    additem(i)
                    i.tags = itemconf.pop('tags').split(      )

                    for key, value in itemconf.items():
                        setattr(i, key, value)
                    self.itemvalues[i]=itemvalue

                except KeyError:
                    try:
                        command = itemconf.pop('command')
                        parameter = itemconf.pop('parameter')
                        if command == 'boilercmd':
                            i = Getsetitem(itemname, itemvalue, setter=lambda item, value, p=parameter:self.boiler_cmd(p))
                            additem(i, 'W')
                            i.tags = itemconf.pop('tags').split()
                            for key, value in itemconf.items():
                                setattr(i, key, value)
                    except KeyError:
                        pass
            except KeyError:
                pass

        i = Storeditem('feeder_capacity', '1500')
        additem(i, 'R/W')
        i.tags = ['All', 'MGM']

        i = Storeditem('efficiency', '90')
        i.longname = 'Efficiency'
        i.unit = '%'
        i.description = 'Efficiency used in burner power calculation. Used for pellet consumption calculation.'
        additem(i, 'R/W')
        i.tags = ['All', 'MGM']

        i = Getsetitem('feeder_time', '0', getter=lambda item:str(int(self.feeder_time)))
        additem(i, 'R')
        i.tags = ['All', 'MGM']

        self.state = 'OK'
        i = Getsetitem('alarm', '0', getter=lambda item:self.state) 
        additem(i, 'R')

        self.update_interval = 0.1

        t = Timer(0, self.update_thread)
        t.setDaemon(True)
        t.start()

    def boiler_cmd(self, param):
        try:
            boilercmd_url = 'http://' + self.db['mgm_ip'].value + self.conf['boilercmd']
            response = requests.get(boilercmd_url +'?'+ param, timeout=5)
        except:
            logger.info('boiler command failed, "boilercmd" missing from conf?')

    def update_thread(self):
        last_update = None
        self.feeder_time = 0
        if self.errorcounter > 100:
            self.errorcounter = 0
        oldmode = None
        while True:
            try:
                status_url = 'http://' + self.db['mgm_ip'].value + self.conf['status']
            except:
                time.sleep(10)
                continue

            sleep(self.update_interval)
            try:
                response = requests.get(status_url, timeout=8)
                if response.status_code == requests.codes.ok:
                    now = monotonic_time()
                    if last_update:
                        time_diff = now - last_update
                        feeder_capacity = float(self.db['feeder_capacity'].value) / 360
                        power = float(self.itemvalues['RATED_POWER'])/10
                        proc_id = self.itemvalues['PROC_ID']
                        try:
                            efficiency = float(self.db['efficiency'].value) / 100
                        except ValueError:
                            efficiency = 1
                        if proc_id == '5':
                            self.feeder_time +=  (power / 4.8 / 3600) * 1000 * time_diff / feeder_capacity / efficiency
                    last_update = now
                    
                    root = et.fromstring(response.text)
                    if self.state == 'Disconnected':
                        logger.info('The burner is connected!')
                    self.state = 'OK'
                    for element in root:
                        text = unicode(element.text)
                        if 'PROC_ID' in self.itemvalues and self.itemvalues['PROC_ID'] != '5' and element.tag == 'RATED_POWER':
                            text = u'0'
                        self.itemvalues[element.tag] = text
                    if not oldmode:
                        oldmode = self.db['mode'].value
                    try:
                        if oldmode != self.db['mode'].value:
                            logger.info('Mode went from %s to %s'%(oldmode, self.db['mode'].value))
                            oldmode = self.db['mode'].value
                    except Exception as e:
                        pass
                else:
                    response.raise_for_status()
            except Exception as e:
                print time(), str(e)
                if self.update_interval < 60:
                    self.update_interval = self.update_interval * 2
                else:
                    if self.errorcounter == 0:
                        self.state = 'Disconnected'
                        logger.info('The burner is disconnected')
                    self.errorcounter +=1
            else:
                self.update_interval = 5
                self.errorcounter = 0
