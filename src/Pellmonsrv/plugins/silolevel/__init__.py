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
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd
import time
from datetime import datetime
from logging import getLogger
from time import mktime
from datetime import datetime
import subprocess
import simplejson as json
import re
import math

logger = getLogger('pellMon')

itemList=[{'name':'silo_reset_level',  'longname':'Silo fill up level',
           'type':'R/W',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'50000'},
          {'name':'silo_reset_time',   'longname':'Silo fill up time', 
           'type':'R/W',   'unit':''    ,   'value':'01/01/14 12:00', 'min':'0', 'max':'-'},
          {'name':'silo_level',   'longname':'Silo level',
           'type':'R',   'unit':'kg'    ,   'value':'0', 'min':'0', 'max':'-'},
         ]

itemTags = {'silo_reset_level' :    ['All', 'Basic', 'SiloLevel'],
            'silo_reset_time' :     ['All', 'Basic', 'SiloLevel'],
            'silo_level' :          ['All', 'Basic', 'SiloLevel'],
           }

itemDescriptions = {'silo_reset_level':     'Silo fill up to this amount',
                    'silo_reset_time' :     'dd/mm/yy hh:mm Automatically set when setting fill up level',
                    'silo_level' :          'Remaining amount of pellets in silo',
                   }

itemValues={}
Menutags = ['SiloLevel']

class silolevelplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        self.updateTime = 0
        self.siloData = None
        self.valuestore = ConfigParser()
        self.valuestore.add_section('values')
        self.valuesfile = path.join(path.dirname(__file__), 'values.conf')
        for item in itemList:
            if item['type'] == 'R/W':
                self.valuestore.set('values', item['name'], item['value'])
            else:
                itemValues[item['name']] = item['value']
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

    def getItem(self, itemName):
        if itemName == 'silo_level':
            print 'sdffff'
            a = self.getItem('siloLevelData')
            return str(int(self.siloData[0]['data'][-1:][0][1] ))
        for i in itemList:
            if i['name'] == itemName:
                return str(self.valuestore.get('values', itemName))
        if itemName == 'siloLevelData':
            return self.graphData()
        return 'error'

    def setItem(self, item, value):
        try:
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                self.valuestore.set('values', item, str(value))
                f = open(self.valuesfile, 'w')
                self.valuestore.write(f)
                f.close()
                if item=='silo_reset_level':
                    d = datetime.fromtimestamp(time())
                    s = d.strftime('%d/%m/%y %H:%M')
                    self.setItem('silo_reset_time', s)
                return 'OK'
        except Exception,e:
            return 'error'

    def getDataBase(self):
        l=[]
        for item in itemList:
            l.append(item['name'])
        l.append('siloLevelData')
        return l

    def GetFullDB(self, tags):

        def match(requiredtags, existingtags):
            for rt in requiredtags:
                if rt != '' and not rt in existingtags:
                    return False
            return True
            
        items = [item for item in itemList if match(tags, itemTags[item['name']]) ]
        items.sort(key = lambda k:k['name'])
        for item in items:
            item['description'] = itemDescriptions[item['name']]
        return items
        
    def getMenutags(self):
        return Menutags

    def graphData(self):
        if time.time() - self.updateTime < 300:
            return json.dumps(self.siloData)
        try:
            reset_level=self.getItem('silo_reset_level')
            reset_time=self.getItem('silo_reset_time')
            reset_time = datetime.strptime(reset_time,'%d/%m/%y %H:%M')
            reset_time = mktime(reset_time.timetuple())
        except:
            return None

        now=str(int(time.time()))
        start=str(int(reset_time))
        db = self.glob['conf'].db
        RRD_command =  ['rrdtool', 'xport', '--json', '--end', now , '--start', start]
        RRD_command.append("DEF:a=%s:feeder_time:AVERAGE"%db)
        RRD_command.append("DEF:b=%s:feeder_capacity:AVERAGE"%db)
        RRD_command.append("CDEF:t=a,POP,TIME")
        RRD_command.append("CDEF:tt=PREV(t)")
        RRD_command.append("CDEF:i=t,tt,-")
        RRD_command.append("CDEF:s1=t,POP,COUNT,1,EQ,%s,0,IF"%reset_level)
        RRD_command.append("CDEF:s=a,b,*,360000,/,i,*")
        RRD_command.append("CDEF:fs=s,UN,0,s,IF")
        RRD_command.append("CDEF:c=s1,0,EQ,PREV,UN,0,PREV,IF,fs,-,s1,IF")
        RRD_command.append("XPORT:c:level")
        cmd = subprocess.Popen(RRD_command, shell=False, stdout=subprocess.PIPE)

        out = cmd.communicate()[0]
        #print out
        out = re.sub(r'(?:^|(?<={))\s*(\w+)(?=:)', r' "\1"', out, flags=re.M)
        out = re.sub(r"'", r'"', out)
        out= json.loads(out)
        data = out['data']
        is_dst = time.daylight and time.localtime().tm_isdst > 0
        utc_offset = - (time.altzone if is_dst else time.timezone)
        
        start = int(out['meta']['start'])*1000
        step = int(out['meta']['step'])*1000
        legends = out['meta']['legend']
        t = start + (utc_offset * 1000)
        flotdata=[]
        for i in range(len(legends)):
            flotdata.append({'label':legends[i], 'data':[]})
        for s in data:
            for i in range(len(s)):
                flotdata[i]['data'].append([t, s[i]])
            t += step
        self.siloData = flotdata
        self.updateTime=time.time()
        return json.dumps(self.siloData)

