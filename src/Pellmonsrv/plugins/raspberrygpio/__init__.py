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
import RPi.GPIO as GPIO
from time import time, sleep
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd
import mmap

itemList=[]
itemTags = {}
Menutags = ['raspberryGPIO']

import signal
import sys

def signal_handler(signal, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

last_edge = 0
oldstate = 1


def root(request, response, itemList):
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

    def timer():
        m.seek(4)
        s =  m.read(8)
        o = 0
        for c in range(0,7):
            o += ord(s[c])<<(8*c)
        return o

    def tacho_callback(channel):
        global last_time
        global buf
        global index
        global f
        global lapse
        time = timer()
        timediff = time - last_time
        last_time = time
        buf[index] = timediff
        if index == 4:
            index = 0
        else:
            index += 1
        lapse += timediff
        l = buf
        l.sort()
        s = l[2]
        if s>1:
            f1 = 1/float(s) * 1000000 * 60
            f=(f + f1) / 2
        else:
            f=0

    GPIO.setmode(GPIO.BOARD)

    signal.signal(signal.SIGINT, signal_handler)
    for item in itemList:
        if item['function'] == 'counter':
            pin = item['pin']
            count = [0]
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=edge_callback)
            global ev
            from threading import Event
            ev = Event()
            t = Thread(target=filter_thread)
            t.setDaemon(True)
            t.start()
            
        elif item['function'] == 'tachometer':
            pin = item['pin']
            mem = open ('/dev/mem','r')
            global m 
            m = mmap.mmap(mem.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ, offset=0x20003000)
            GPIO.setup(pin, GPIO.IN)
            global f
            f = 0
            global buf
            buf = [0,0,0,0,0]
            global index
            index = 0
            global last_time
            last_time=timer()
            global lapse
            lapse = 0
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=tacho_callback)

        elif item['function'] == 'input':
            pass
        elif item['function'] == 'output':
            pass

    x = request.get()
    while not x=='quit':
        if x == 'tachometer':
            response.put(int(f))
        elif x == 'counter':
            response.put(int(count[0]))
        else:
            try:
                if x[0] == 'counter':
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
        self.power = 0

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.pin2index={}
        self.name2index={}
        for key,value in self.conf.iteritems():
            try:
                pin_name = key.split('_')[0]
                pin_data = key.split('_')[1]
                if not self.pin2index.has_key(pin_name):
                    itemList.append({'min':'', 'max':'', 'unit':'', 'type':'R/W', 'description':''})
                    self.pin2index[pin_name] = len(itemList)-1
                if pin_data == 'function':
                    itemList[self.pin2index[pin_name]]['function'] = value
                elif pin_data == 'item':
                    itemList[self.pin2index[pin_name]]['name'] = value
                    itemTags[value] = ['All', 'raspberryGPIO', 'Basic']
                    self.name2index[value]=len(itemList)-1
                elif pin_data == 'pin':
                    itemList[self.pin2index[pin_name]]['pin'] = int(value)
            except Exception,e:
                logger.info(str(e))
        self.request = Queue()
        self.response = Queue()
        self.p = Process(target=root, args=(self.request, self.response, itemList))
        self.p.start()

    def deactivate(self):
        protocols.deactivate(self)
        self.request.put('quit')
        self.p.join()
        GPIO.cleanup()

    def getItem(self, item):
        if self.name2index.has_key(item):
            function =itemList[self.name2index[item]]['function']
            if function in['counter', 'tachometer']:
                self.request.put(function)
                try:
                    return str(self.response.get(0.2))
                except:
                    return str('timeout') 
            else:
                return 'error'
        else:
            return 'error'

    def setItem(self, item, value):
        if self.name2index.has_key(item):
            if itemList[self.name2index[item]]['function'] == 'counter':
                self.request.put(('count', value))
                try:
                    r = self.response.get(5)
                except:
                    r='timeout'
                return str(r)
        else:
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
            item['description'] = ''
        return items
        
    def getMenutags(self):
        return Menutags


