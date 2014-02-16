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
from threading import Thread, Timer, Event, Lock
import RPi.GPIO as GPIO
from time import time, sleep
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd
import mmap
import signal
import sys

itemList=[]
itemTags = {}
Menutags = ['raspberryGPIO']


def signal_handler(signal, frame):
    """ GPIO needs cleaning up on exit """
    GPIO.cleanup()
    sys.exit(0)

class gpio_input(Thread):
    def __init__(self, pin):
        Thread.__init__(self)
        self.pin = pin
        self.ev = Event()
        self.state = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback = self.edge_callback)
        self.setDaemon(True)
        self.start()
        self.state = GPIO.input(self.pin)

    def read(self):
        return self.state

    def edge_callback(self, channel):
        """Called by RpiGPIO interrupt handle on """
        self.last_edge = time()
        self.ev.set()

    def run(self):
        """Handle debounce filtering of the inputs"""
        while True:
            self.ev.wait()
            if time() - self.last_edge > 0.1:
                self.ev.clear()
                self.state = GPIO.input(self.pin)
            else:
                 sleep(0.05)

class gpio_latched_input(Thread):
    def __init__(self, pin):
        Thread.__init__(self)
        self.pin = pin
        self.ev = Event()
        self.state = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback = self.edge_callback)
        self.setDaemon(True)
        self.start()
        self.last_read = GPIO.input(self.pin)
        self.latched_state = self.last_read
        self.current_state = self.last_read
        self.mutex = Lock()

    def read(self):
        state = self.latched_state
        self.mutex.acquire()
        self.last_read = state
        self.latched_state = self.current_state
        self.mutex.release()
        return state

    def edge_callback(self, channel):
        """Called by RpiGPIO interrupt handle on """
        self.last_edge = time()
        self.ev.set()

    def run(self):
        """Handle debounce filtering of the inputs"""
        while True:
            self.ev.wait()
            if time() - self.last_edge > 0.1:
                self.ev.clear()
                self.mutex.acquire()
                self.current_state = GPIO.input(self.pin)
                if self.current_state != self.last_read:
                    self.latched_state = self.current_state
                self.mutex.release()
            else:
                 sleep(0.05)

class gpio_counter(Thread):
    def __init__(self, pin):
        Thread.__init__(self)
        self.pin = pin
        self.ev = Event()
        self.count = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback = self.edge_callback)
        self.setDaemon(True)
        self.start()

    def read(self):
        return self.count

    def write(self, value):
        self.count = value
        return ('OK')

    def edge_callback(self, channel):
        """Called by RpiGPIO interrupt handle on """
        self.last_edge = time()
        self.ev.set()

    def run(self):
        """Handle debounce filtering of the inputs"""
        while True:
            self.ev.wait()
            if time() - self.last_edge > 0.1:
                self.ev.clear()
                currentstate = GPIO.input(self.pin)
                if currentstate == 0:
                    self.count += 1
            else:
                 sleep(0.05)

class gpio_tachometer(Thread):
    def __init__(self, pin):
        Thread.__init__(self)
        self.pin = pin
        self.buf = [0]*500
        self.index = 0
        self.f = 0
        GPIO.setup(pin, GPIO.IN)

        mem = open ('/dev/mem','r')
        self.m = mmap.mmap(mem.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ, offset=0x20003000)

        self.last_time= self.timer()
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback = self.tacho_callback)

        self.setDaemon(True)
        self.start()

    def timer(self):
        """Read the 64bit freerunning megaherz timer of the broadcom chip"""
        self.m.seek(4)
        s =  self.m.read(8)
        o = 0
        for c in range(0,7):
            o += ord(s[c])<<(8*c)
        return o

    def read(self):
        buf = list(self.buf)
        index = self.index
        i = index
        lapse = 0
        while i>0 and lapse < 10500000:
            lapse += buf[i]
            i-= 1
        b = buf[i:index] 
        i = 499
        if lapse < 10500000:
            while i>index and lapse < 10500000:
                lapse += buf[i]
                i-=1
            b += buf[i:500]
        b.sort()
        l = len(b)-1
        if l>30:
            s = b[20]
        else:
            s = b[0]
        if s>1:
            self.f = 1/float(s) * 1000000 * 60
        else:
            self.f=0
        return self.f

    def tacho_callback(self, channel):
        """Called by falling edge interrupt on the tachometer input to calculate rpm"""
        time = self.timer()
        timediff = time - self.last_time
        self.last_time = time
        self.buf[self.index] = timediff
        if self.index == 499:
            self.index = 0
        else:
            self.index += 1

    def run(self):
        """ """
        while True:
            sleep(5)

class gpio_output(object):
    def __init__(self, pin):
        self.pin = pin
        self.value = 0
        GPIO.setup(self.pin, GPIO.OUT)

    def read(self):
        return str(self.value)

    def write(self, value):
        if value == '0':
            self.value = 0
        else:
            self.value = 1
        GPIO.output(self.pin, self.value)
        return 'OK'

class root(Process):
    """GPIO needs root, so we fork off this process before the server drops privileges"""
    def __init__(self, request, response, itemList):
        Process.__init__(self)
        self.request = request
        self.response = response
        self.itemList = itemList
        self.pin={}

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        signal.signal(signal.SIGINT, signal_handler)

        for item in itemList:
            pin = item['pin']
            if item['function'] == 'counter':
                self.pin[pin] = gpio_counter(pin)
            elif item['function'] == 'tachometer':
                self.pin[pin] = gpio_tachometer(pin)
            elif item['function'] == 'input':
                self.pin[pin] = gpio_input(pin)
            elif item['function'] == 'latched_input':
                self.pin[pin] = gpio_latched_input(pin)
            elif item['function'] == 'output':
                self.pin[pin] = gpio_output(pin)

        #Wait for a request 
        req = self.request.get()
        while not req=='quit':
            try:
                if req[0] == 'read':
                    self.response.put(self.pin[req[1]].read())
                if req[0] == 'write':
                    self.response.put(self.pin[req[1]].write(req[2]))
            except:
                self.response.put('error')
            req=self.request.get()

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
                    itemList.append({'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})
                    self.pin2index[pin_name] = len(itemList)-1
                if pin_data == 'function':
                    itemList[self.pin2index[pin_name]]['function'] = value
                    if value in ['counter', 'output']:
                        itemList[self.pin2index[pin_name]]['type'] = 'R/W'
                elif pin_data == 'item':
                    itemList[self.pin2index[pin_name]]['name'] = value
                    itemTags[value] = ['All', 'raspberryGPIO', 'Basic']
                    self.name2index[value]=self.pin2index[pin_name]
                elif pin_data == 'pin':
                    itemList[self.pin2index[pin_name]]['pin'] = int(value)
            except Exception,e:
                logger.info(str(e))
        signal.signal(signal.SIGINT, signal_handler)
        self.request = Queue()
        self.response = Queue()
        self.root = root(self.request, self.response, itemList)
        self.root.start()

    def deactivate(self):
        protocols.deactivate(self)
        self.request.put('quit')
        self.root.join()
        GPIO.cleanup()

    def getItem(self, item):
        if self.name2index.has_key(item):
            function = itemList[self.name2index[item]]['function']
            pin = itemList[self.name2index[item]]['pin']
            if function in['counter', 'tachometer', 'input', 'latched_input', 'output']:
                self.request.put(('read', pin))
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
            if itemList[self.name2index[item]]['function'] in ['counter', 'output']:
                pin = itemList[self.name2index[item]]['pin']
                self.request.put(('write', pin, value))
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


