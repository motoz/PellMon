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
from os import path
import os, grp, pwd
import time
from datetime import datetime, timedelta
from logging import getLogger
from time import mktime
import subprocess
import simplejson as json
import re
import math
import random
from Pellmonsrv.database import Item, Getsetitem

logger = getLogger('pellMon')

itemList=[#{'name':'clean_after',  'longname':'Clean after',
          # 'type':'R/W',   'unit':'kg'   ,   'value':'1000', 'min':'0', 'max':'10000'},
          {'name':'clean_time',   'longname':'Last cleaning time', 
           'type':'R/W',   'unit':''    ,   'value':'01/01/14 12:00', 'min':'0', 'max':'-'},
          {'name':'clean_kg',     'longname':'Cleaning counter',
           'type':'R',   'unit':'kg'    ,   'value':'0', 'min':'0', 'max':'-'},
          #{'name':'clean_days',   'longname':'Cleaning days left',
          # 'type':'R',   'unit':'days'    ,   'value':'0', 'min':'0', 'max':'-'},
          {'name':'clean',        'longname':'Clean now',
           'type':'W',   'unit':''    ,   'value':'0', 'min':'0', 'max':'0'},
         ]

itemTags = {'clean_after' :    ['All', 'Basic', 'Cleaning'],
            'clean_time' :     ['All', 'Basic', 'Cleaning'],
            'clean_kg' :       ['All', 'Basic', 'Cleaning', 'Overview'],
            'clean_days' :     ['All', 'Basic', 'Cleaning'],
            'clean' :          ['All', 'Basic', 'Cleaning'],
           }

itemDescriptions = {'clean_after':     'Clean the boiler after this amount burned',
                    'clean_time' :     'dd/mm/yy hh:mm Time when the boiler was cleaned',
                    'clean_kg'   :     'Amount burned since last cleaning',
                    'clean_days' :     'Remaining days until the boiler should be cleaned',
                    'clean'      :     'Set clean_time to now',
                   }

itemValues={}
Menutags = ['Cleaning']

class cleaningplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)
        self.items = {i['name']:i for i in itemList}
        self.rrdfile = self.glob['conf'].db
        self.feeder_time = self.glob['conf'].item_to_ds_name['feeder_time']
        self.feeder_capacity = self.glob['conf'].item_to_ds_name['feeder_capacity']
        self.itemrefs = []
        for item in itemList:
            dbitem = Getsetitem(item['name'], lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
            for key, value in item.iteritems():
                dbitem.__setattr__(key, value)
            if dbitem.name in itemTags:
                dbitem.__setattr__('tags', itemTags[dbitem.name])
            self.db.insert(dbitem)
            self.itemrefs.append(dbitem)

            if item['type'] == 'R/W':
                self.store_setting(item['name'], confval = item['value'])
            else:
                itemValues[item['name']] = item['value']
        self.migrate_settings('cleaning')

    def getItem(self, itemName):
        item = self.items[itemName]
        if itemName == 'clean_kg':
            now = int(time.time())
            if 'update_time' not in item or now - item['update_time'] > 600:
                start = self.getItem('clean_time')
                start = datetime.strptime(start,'%d/%m/%y %H:%M')
                start = int(mktime(start.timetuple()))
                try:
                    item['value'] = self.rrd_total(start, now)
                    item['update_time'] = now
                    return item['value']
                except Exception, e:
                    return str(e)
            else:
                return item['value']
        else:
            if itemName in self.items and item['type'] == 'R/W':
                return str(self.load_setting(itemName))
            else:
                return 'error'

    def setItem(self, item, value):
        try:
            if item == 'clean':
                d = datetime.fromtimestamp(time.time())
                s = d.strftime('%d/%m/%y %H:%M')
                self.setItem('clean_time', s)
                return 'OK'
            elif item == 'clean_time':
                self.items['clean_kg']['update_time'] = 0
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                try:
                    t = datetime.strptime(value,'%d/%m/%y %H:%M')
                    self.store_setting(item, str(value))
                    return 'OK'
                except Exception,e:
                    return 'error'
        except Exception,e:
            return 'error'

    def getMenutags(self):
        return Menutags

    def rrd_total(self, start, end):
        start = str(start)
        end = str(end)
        command = ['rrdtool', 'graph', '--start', start, '--end', end,'-', 'DEF:a=%s:%s:AVERAGE'%(self.rrdfile,self.feeder_time),'DEF:b=%s:%s:AVERAGE'%(self.rrdfile,self.feeder_capacity), 'CDEF:c=a,b,*,360000,/', 'VDEF:s=c,TOTAL', 'PRINT:s:\"%lf\"']
        cmd = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
        try:
            total = str(int(float(cmd.communicate()[0].splitlines()[1].strip('"'))))
        except Exception, e:
            total = '0'
        return total

