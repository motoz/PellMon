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
from threading import Thread 
import RPi.GPIO as GPIO
from time import time, sleep
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd

itemList=[{'name':'feeder_rev_capacity',  'longname':'feeder capacity',       'type':'R',   'unit':'g'   ,   'value': 5.56 },
          {'name':'feeder_rpm',           'longname':'feeder rpm',            'type':'R',   'unit':'/60s',   'value': 30   },
          
          {'name':'feeder_capacity',      'longname':'feeder 6 min capacity', 'type':'R/W', 'unit':'g/360s', 'value': 1000, 'min':'0', 'max':'5000' },
          {'name':'feeder_rp6m',          'longname':'feeder rev per 6 min',  'type':'R/W', 'unit':'/360s',  'value': 180,  'min':'0', 'max':'500'  },
          
          {'name':'feeder_rev',           'longname':'feeder rev count',      'type':'R/W', 'unit':' ',      'value': 0,    'min':'0', 'max':'-'    },
          {'name':'feeder_time',          'longname':'feeder time',           'type':'R',   'unit':'s',      'value': 0    }
         ]

itemTags = {'feeder_rev_capacity' : ['All', 'raspberryGPIO'],
            'feeder_rpm' :          ['All', 'raspberryGPIO'],
            'feeder_capacity' :     ['All', 'raspberryGPIO', 'Basic'],
            'feeder_rp6m' :         ['All', 'raspberryGPIO', 'Basic'],
            'feeder_rev' :          ['All', 'raspberryGPIO', 'Basic'],
            'feeder_time' :         ['All', 'raspberryGPIO'],
           }

itemDescriptions = {'feeder_rev_capacity' : 'Average grams fed in one revolution',
                    'feeder_rpm' :          'Feeder screw rotation speed',
                    'feeder_capacity' :     'Grams fed in 360 seconds',
                    'feeder_rp6m' :         'Feeder screw revolutions in 360 seconds',
                    'feeder_rev' :          'Feeder screw revolutions count',
                    'feeder_time' :         'Feeder screw run time'}

Menutags = ['raspberryGPIO']

import signal
import sys
def signal_handler(signal, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

last_edge = 0
oldstate = 1

def root(request, response):
    def edge_callback(channel):
        global last_edge
        last_edge = time()
        ev.set()

    def filter_thread():
        while True:
            global event
            ev.wait()
            if time() - last_edge > 0.1:
                ev.clear()
                currentstate = GPIO.input(26)
                global oldstate     
                if currentstate == 0 and oldstate == 1:
                    count[0] += 1
                state = 0
            else:
                 sleep(0.05)

    signal.signal(signal.SIGINT, signal_handler)
    count = [0]
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(26, GPIO.FALLING, callback=edge_callback)
    global ev
    from threading import Event
    ev = Event()
    t = Thread(target=filter_thread)
    t.setDaemon(True)
    t.start()

    x = request.get()
    while not x=='quit':
        if x == 'count':
            response.put(int(count[0]))
        else:
            try:
                if x[0] == 'count':
                    count[0] = int(x[1])
                    response.put('OK')
                else:
                    response.put('what?')
            except:
                response.put('error')
        x=request.get()

class raspberry_gpio(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.request = Queue()
        self.response = Queue()
        self.p = Process(target=root, args=(self.request, self.response))
        self.p.start()
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

    def deactivate(self):
        protocols.deactivate(self)
        self.request.put('quit')
        self.p.join()
        GPIO.cleanup()

    def getItem(self, item):
        if item == 'feeder_rev':
            self.request.put('count')
            try:
                return str(self.response.get(0.2))
            except:
                return str('timeout') 
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
        else:
            for i in itemList:
                if i['name'] == item:
                    return str(self.valuestore.get('values', item))

    def setItem(self, item, value):
        if item == 'feeder_rev':
            self.request.put(('count', value))
            try:
                r = self.response.get(5)
            except:
                r='timeout'
            return str(r)
        else:
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


