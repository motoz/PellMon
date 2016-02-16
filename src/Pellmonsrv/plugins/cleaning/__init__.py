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
from Pellmonsrv.database import Getsetitem, Storeditem, Cacheditem
import time
from datetime import datetime
from logging import getLogger
import subprocess

logger = getLogger('pellMon')

Menutags = ['Cleaning']

class cleaningplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)

        self.rrdfile = self.glob['conf'].db
        self.feeder_time = self.glob['conf'].item_to_ds_name['feeder_time']
        self.feeder_capacity = self.glob['conf'].item_to_ds_name['feeder_capacity']
        self.itemrefs = []

        self.migrate_settings('cleaning')

        i = Cacheditem('clean_kg', 0, getter = lambda i:self.get_kg(i), timeout = 600)
        i.longname = 'Cleaning counter'
        i.type = 'R'
        i.unit = 'kg'
        i.description = 'Amount burned since last cleaning'
        i.tags = ['All', 'Basic', 'Cleaning', 'Overview']
        self.db.insert(i)
        self.itemrefs.append(i)

        i = Storeditem('clean_time', '01/01/14 12:00', setter = lambda i,v:self.set_time(i,v))
        i.longname = 'Last cleaning time'
        i.type = 'R/W'
        i.description = 'dd/mm/yy hh:mm Time when the boiler was cleaned'
        i.tags = ['All', 'Basic', 'Cleaning']
        self.db.insert(i)
        self.itemrefs.append(i)
        
        i = Getsetitem('clean', '-', setter = lambda i,v:self.clean_now(i,v))
        i.type = 'W'
        i.tags = ['All', 'Basic', 'Cleaning']
        self.db.insert(i)
        self.itemrefs.append(i)

    def clean_now(self, item, value):
        d = datetime.fromtimestamp(time.time())
        s = d.strftime('%d/%m/%y %H:%M')
        self.db['clean_time'].value = s

    def set_time(self, item, value):
        t = self.db['clean_kg'].uncached_value

    def get_kg(self, item):
        now = int(time.time())
        start = self.db['clean_time'].value
        start = datetime.strptime(start,'%d/%m/%y %H:%M')
        start = int(time.mktime(start.timetuple()))
        return self.rrd_total(start, now)

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

