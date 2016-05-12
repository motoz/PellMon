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
from Pellmonsrv.database import Getsetitem, Storeditem, Cacheditem, Plainitem
import time
from logging import getLogger
from threading import Thread

logger = getLogger('pellMon')

Menutags = ['Heating circuit']

class Heatingcircuitplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)

        self.itemrefs = []

        for key, value in self.conf.iteritems():
            if key == 'output_open':
                self.output_open = value
            if key == 'output_close':
                self.output_close = value
            if key == 'hctemp':
                self.hctemp_item = value
            if key == 'outside_temp':
                self.outside_temp = value

        def additem(i):
            i.tags = ['All', 'Basic', 'Heating circuit']
            i.type = 'R/W'
            i.min = ''
            i.max = ''
            self.db.insert(i)
            self.itemrefs.append(i)

        additem(Plainitem('desired_hctemp', 20))
        additem(Plainitem('hc_out', 30))
        additem(Storeditem('curve_1x', -20))
        additem(Storeditem('curve_1y', 60))
        additem(Storeditem('curve_2x', 20))
        additem(Storeditem('curve_2y', 20))
        additem(Storeditem('hc_gain', 8))

        self.desired_temp = float(self.db[self.hctemp_item].value)

        self.feedforwardthread = Thread(target = lambda:self.feedforward())
        self.feedforwardthread.setDaemon(True)
        self.feedforwardthread.start()

        self.valvecontrollerthread = Thread(target = lambda:self.valvecontroller())
        self.valvecontrollerthread.setDaemon(True)
        self.valvecontrollerthread.start()

        self.controllerthread = Thread(target = lambda:self.controller())
        self.controllerthread.setDaemon(True)

    def getMenutags(self):
        return Menutags

    def controller(self):
        """Calculate the controller output signal"""
        while True:
            try:
                t = time.time()
                gain_P = float(self.db['hc_gain'].value)
                err = self.desired_temp - self.hctemp
                if abs(err) < 0.5:
                    err = 0
                out = gain_P * err
                self.db['hc_out'].value = str(out)
                time.sleep(1.0 - (time.time() - t))
            except Exception,e:
                logger.info(str(e))

    def valvecontroller(self):
        """Handle the valve motor outputs"""
        def sleep(t):
            time.sleep(t/100.0*5)        
        hc_out_saved = 0
        while True:
            output_open = self.db[self.output_open]
            output_close = self.db[self.output_close]
            hc_out = float(self.db['hc_out'].value)
            hc_out += hc_out_saved
            try:
                if hc_out > 20 or hc_out < -20:
                    if hc_out > 0:
                        output = output_open
                    else:
                        hc_out = hc_out * -1
                        output = output_close
                    if hc_out > 100:
                        hc_out = 100
                    t_0 = time.time()
                    output.value = '1'
                    sleep(hc_out)
                    output.value = '0'
                    hc_out_saved = 0
                    sleep(100 - hc_out)
                else:
                    # small steps are collected until there is at least one second
                    hc_out_saved += hc_out
                    sleep(100)
            except Exception, e:
                logger.info(str(e))

    def feedforward(self):
        """Handle outside temperature compensation"""
        firstrun = True
        while True:
            try:
                outside_temp = float(self.db[self.outside_temp].value)
                self.hctemp = float(self.db[self.hctemp_item].value)

                temp_x1 = float(self.db['curve_1x'].value)
                temp_y1 = float(self.db['curve_1y'].value)
                temp_x2 = float(self.db['curve_2x'].value)
                temp_y2 = float(self.db['curve_2y'].value)

                self.desired_temp = (outside_temp - temp_x1) / (temp_x2 - temp_x1) * (temp_y2 - temp_y1) + temp_y1
                self.db['desired_hctemp'].value = unicode(self.desired_temp)

                if firstrun:
                    self.controllerthread.start()
                    firstrun = False
            except Exception, e:
                if  self.glob['conf'].command == 'debug':
                    raise
                logger.info(str(e))
            time.sleep(10)

