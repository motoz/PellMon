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
from multiprocessing import Process, Queue
from threading import Thread, Timer
from time import time, sleep
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd
import sys

itemList=[{'name':'feeder_rev_capacity',  'longname':'feeder capacity',          'type':'R',   'unit':'g'   ,   'value': 5.56 },
          {'name':'feeder_rpm',           'longname':'feeder rpm',               'type':'R',   'unit':'/60s',   'value': 30   },
          
          {'name':'feeder_capacity',      'longname':'feeder 6 min capacity',    'type':'R/W', 'unit':'g/360s', 'value': 1000, 'min':'0', 'max':'5000' },
          {'name':'feeder_rp6m',          'longname':'feeder rev per 6 min',     'type':'R/W', 'unit':'/360s',  'value': 180,  'min':'0', 'max':'500'  },
          
          {'name':'feeder_rev',           'longname':'feeder rev count',         'type':'R',   'unit':' ',      'value': '',    'min':'0', 'max':'-'    },
          {'name':'feeder_time',          'longname':'feeder time',              'type':'R',   'unit':'s',      'value': 0    },
          {'name':'power_kW',             'longname':'power',                    'type':'R',   'unit':'kW',     'value': 0    }, 
         ]

itemTags = {'feeder_rev_capacity' : ['All', 'pelletCalc'],
            'feeder_rpm' :          ['All', 'pelletCalc'],
            'feeder_capacity' :     ['All', 'pelletCalc', 'Basic'],
            'feeder_rp6m' :         ['All', 'pelletCalc', 'Basic'],
            'feeder_rev' :          ['All', 'pelletCalc', 'Basic'],
            'feeder_time' :         ['All', 'pelletCalc'],
            'power_kW' :            ['All', 'pelletCalc'],
           }

itemDescriptions = {'feeder_rev_capacity' : 'Average grams fed in one revolution',
                    'feeder_rpm' :          'Feeder screw rotation speed',
                    'feeder_capacity' :     'Grams fed in 360 seconds',
                    'feeder_rp6m' :         'Feeder screw revolutions in 360 seconds',
                    'feeder_rev' :          'Feeder screw revolutions count',
                    'feeder_time' :         'Feeder screw run time',
                    'power_kW' :            'Power calculated from fed pellet mass/time'}

Menutags = ['pelletCalc']


class pelletcalc(protocols):
    def __init__(self):
        protocols.__init__(self)
        self.timelist=[]
        self.power = 0

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.valuestore = ConfigParser()
        self.valuestore.add_section('values')
        self.valuesfile = path.join(path.dirname(__file__), 'values.conf')
        for item in itemList:
            self.valuestore.set('values', item['name'], item['value'])
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

        t = Timer(5, self.calc_thread)
        t.setDaemon(True)
        t.start()

    def deactivate(self):
        protocols.deactivate(self)

    def getItem(self, item):
        if item == 'feeder_rev':
            return self.getGlobalItem(self.conf['counter'])
        elif item == 'feeder_time':
            rev = float(self.getItem('feeder_rev'))
            rp6m = int(self.getItem('feeder_rp6m'))
            time_per_rev = (360.0 / rp6m)
            return str(int(rev * time_per_rev))
        elif item == 'feeder_rev_capacity':
            capacity = float(self.getItem('feeder_capacity'))
            rp6m = float(self.getItem('feeder_rp6m'))
            return str(capacity / rp6m)
        elif item == 'feeder_rpm':
            rp6m = int(self.getItem('feeder_rp6m'))
            return str(rp6m / 6.0)
        elif item == 'power_kW':
            return str(self.power)
        else:
            for i in itemList:
                if i['name'] == item:
                    return str(self.valuestore.get('values', item))

    def setItem(self, item, value):
        for i in itemList:
            if i['name'] == item:
                i['value'] = value
                self.valuestore.set('values', item, str(value))
                f = open(self.valuesfile, 'w')
                self.valuestore.write(f)
                f.close()
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
            item['description'] = itemDescriptions[item['name']]
        return items
        
    def getMenutags(self):
        return Menutags

    def calc_thread(self):
        """ Calculate last 5 minutes mean power """
        p1 = int(self.getItem('feeder_time'))
        t1 = time()
        self.timelist.append((p1,t1))
        if self.timelist[-1][1] - self.timelist[0][1] > 300:
            self.timelist = self.timelist[1:]
        last = self.timelist[0][0]
        sum = 0
        for t in self.timelist:
             try:
                 v = int(t[0])
             except:
                 v = 0
             if v > last:
                 sum += (v - last)
             last = v
        capacity = float(self.getItem('feeder_capacity')) / 360
        self.power = sum * capacity * 12 * 4.8 * 0.9 / 1000

        t = Timer(5, self.calc_thread)
        t.setDaemon(True)
        t.start()
