#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published b
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
#from threading import Thread, Timer
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

itemList=[{'name':'silo_reset_level',  'longname':'Silo fill up level',
           'type':'R/W',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'50000'},
          {'name':'silo_reset_time',   'longname':'Silo fill up time', 
           'type':'R/W',   'unit':''    ,   'value':'01/01/14 12:00', 'min':'0', 'max':'-'},
          {'name':'silo_level',   'longname':'Silo level',
           'type':'R',   'unit':'kg'    ,   'value':'0', 'min':'0', 'max':'-'},
          {'name':'silo_days_left',   'longname':'Silo days left',
           'type':'R',   'unit':'days'    ,   'value':'0', 'min':'0', 'max':'-'},
         ]

itemTags = {'silo_reset_level' :    ['All', 'Basic', 'SiloLevel'],
            'silo_reset_time' :     ['All', 'Basic', 'SiloLevel'],
            'silo_level' :          ['All', 'Basic', 'SiloLevel'],
            'silo_days_left' :      ['All', 'Basic', 'SiloLevel'],
           }

itemDescriptions = {'silo_reset_level':     'Silo fill up to this amount',
                    'silo_reset_time' :     'dd/mm/yy hh:mm Automatically set when setting fill up level',
                    'silo_level' :          'Remaining amount of pellets in silo',
                    'silo_days_left' :      'Remaining days until the silo is empty',
                   }

itemValues={}
Menutags = ['SiloLevel']

class silolevelplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)
        self.updateTime = 0
        self.siloData = None
        self.silo_days_left = None
        self.silo_level = 0
        try:
            self.feeder_time = self.glob['conf'].item_to_ds_name['feeder_time']
        except Exception, e:
            logger.info('Silolevel plugin error: feeder_time is missing from the database')
            raise
        try:
            self.feeder_capacity = self.glob['conf'].item_to_ds_name['feeder_capacity']
        except Exception, e:
            logger.info('Silolevel plugin error: feeder_capacity is missing from the database')
            raise
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
                self.store_setting(item['name'], confval = str(item['value']))
            else:
                itemValues[item['name']] = item['value']

        self.migrate_settings('silolevel')

        self._insert_template('silolevel', """
<h4>Silo level</h4>
<div class="image-responsive" id="silolevel" style="height:400px">
</div>

<script type="text/javascript">
var refreshSilolevel = function() {
    $.get(
        'flotsilolevel',
        function(jsondata) {
            var data = JSON.parse(jsondata);
            var graph = $('#silolevel');
            plot = $.plot(graph, data.graphdata, siloleveloptions);
            $('<p>' + 'current level: ' + data.silo_level + ' kg' + '</p>').insertAfter(graph);
            $('<p>' + data.silo_days_left + ' days to empty' + '</p>').insertAfter(graph).css('float', 'right');
        })
}

var siloleveloptions = {
        series: {
                    lines: { show: true, lineWidth: 1, fill: true, fillColor: "rgba(105, 137, 183, 0.6)"},
                    color:"rgba(105, 137, 183, 0)",
                    points: { show: false },
                    shadowSize: 0,
                },
        xaxes:  [{
                    mode: "time",       
                    position: "bottom",
                }],
        legend: { 
                    show: false,
                },
        grid:   {
                hoverable: true,
                backgroundColor:'#f9f9f9',
                borderWidth: 1,
                borderColor: '#e7e7e7'
                },
    };

document.addEventListener("DOMContentLoaded", function(event) { 
    refreshSilolevel();
});

</script>

""")

    def getItem(self, itemName):
        #print 'getItem called', itemName
        if itemName == 'silo_level':
            self.getItem('siloLevelData')
            return str(self.silo_level)
        elif itemName == 'silo_days_left':
            self.getItem('siloLevelData')
            return self.silo_days_left
        if itemName == 'siloLevelData':
            return self.graphData()
        return self.load_setting(itemName)

    def setItem(self, item, value):
        try:
            self.updateTime = 0
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                self.store_setting(item, str(value))
                if item=='silo_reset_level':
                    d = datetime.fromtimestamp(time.time())
                    s = d.strftime('%d/%m/%y %H:%M')
                    self.setItem('silo_reset_time', s)
                return 'OK'
        except Exception,e:
            return 'error'

    def getMenutags(self):
        return Menutags

    def graphData(self):

        def getLastUpdateTime():
            db = self.glob['conf'].db
            RRD_command =  ['rrdtool', 'last', db]
            cmd = subprocess.Popen(RRD_command, shell=False, stdout=subprocess.PIPE)
            out = cmd.communicate()[0]  
            return int(out)
            
        def siloLevelData(from_time, to_time, from_level):
            db = self.glob['conf'].db
            RRD_command =  ['rrdtool', 'xport', '--json', '--end', str(int(to_time)) , '--start', str(int(from_time))]
            RRD_command.append("DEF:a=%s:%s:AVERAGE"%(db, self.feeder_time))            # a = feeder_time
            RRD_command.append("DEF:b=%s:%s:AVERAGE"%(db, self.feeder_capacity))        # b = feeder_capacity
            RRD_command.append("CDEF:t=a,POP,TIME")                                     # t = time
            RRD_command.append("CDEF:tt=PREV(t)")                                       # tt = time shifted one step
            RRD_command.append("CDEF:i=t,tt,-")                                         # i = time between steps
            RRD_command.append("CDEF:s=a,b,*,360000,/,i,*")                             # s = kg burned between steps
            RRD_command.append("CDEF:fs=s,UN,0,s,IF")                                   # fs = s with unknowns replaced with zeros
            RRD_command.append("CDEF:c=COUNT,1,GT,PREV,fs,-,%s,IF"%str(from_level))     # c = silo_reset_level at first position
                                                                                        # then subtract fs from previous value       

            RRD_command.append("XPORT:c:level")
            cmd = subprocess.Popen(RRD_command, shell=False, stdout=subprocess.PIPE)
            out = cmd.communicate()[0]
            out = re.sub(r'(?:^|(?<={))\s*(\w+)(?=:)', r' "\1"', out, flags=re.M)
            out = re.sub(r"'", r'"', out)
            out= json.loads(out)
            return out

        def getFutureData(start, period, level):
            future = siloLevelData(start-3600*24*365, start+period-3600*24*365, level)
            data = future['data']
            futuredata=[]
            start = (int(future['meta']['start']) + 3600*24*365)*1000
            step = int(future['meta']['step'])*1000
            t = start + (utc_offset * 1000)
            for s in data:
                for i in range(len(s)):
                    futuredata.append([t, s[i]])
                t += step
            level = float(futuredata[-1][1])
            return futuredata, level

        def decimateData(data, maxlen):
            dl = []
            dec = len(data) / maxlen
            if dec > 1:
                for i in xrange(len(data)/dec):
                    dl.append(data[i*dec])
                dl.append(data[-1])
                return dl
            else:
                return data

        try:
            if time.time() - self.updateTime < 300:
                return json.dumps(self.siloData)
            reset_level=self.getItem('silo_reset_level')
            reset_time=self.getItem('silo_reset_time')
            reset_time = datetime.strptime(reset_time,'%d/%m/%y %H:%M')
            reset_time = mktime(reset_time.timetuple())
        except Exception, e:
            return None
        p = int(self.glob['conf'].poll_interval)
        try:
            now = getLastUpdateTime()
        except ValueError:
            now=int(time.time())
        start=int(reset_time)
        out = siloLevelData(start, now, reset_level)

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
        t -= step
        start_prediction_at = t/1000
        flotdata[0]['data'] = decimateData(flotdata[0]['data'], 50)

        # current level
        level = float(flotdata[0]['data'][-1][1])
        self.silo_level = int(level)

        futuredata = {
            'label':'future',
            'data':[],
            'lines':{'fillColor': "rgba(225, 225, 225, 0.6)"}
        }

        try:
            w_data = json.loads(self.db.get_value('consumptionData8w'))['bardata']
            last_month = 0
            for data in w_data:
                if data['label'] == 'last 8':
                    if data['data'][3][1] > 2:
                        last_month = data['data'][4][1] + data['data'][5][1] + data['data'][6][1] + data['data'][7][1]

            last_week = 0
            w_data = json.loads(self.db.get_value('consumptionData7d'))['bardata']
            for data in w_data:
                if data['label'] == 'last 7':
                    last_week = data['data'][1][1] + data['data'][2][1] + data['data'][3][1] + data['data'][4][1] + data['data'][5][1] + data['data'][6][1]*2
            logger.debug('last month: %s, last week: %s'%(last_month, last_week))

            year_old_data = False
            year_data = json.loads(self.db.get_value('consumptionData1y'))['bardata']
            for data in year_data:
                # if there is consumption logged a year ago, use that to make an estimation
                if data['label'] == 'last 12':
                    if data['data'][0][1] > 10:
                        year_old_data = True

            # make an estimate based on last weeks consumption when there is less than three weeks left
            if self.silo_level < last_week * 3:
                logger.debug('last week estimate %s'%last_week)
                level = self.silo_level
                t = start_prediction_at
                while level > 0:
                    futuredata['data'].append([t*1000, level])
                    level = level - last_week / (7*24)
                    t += 3600
                self.silo_days_left = str(int((t - start_prediction_at) / (3600*24)))
                futuredata['data'] = decimateData(futuredata['data'], 50)
                flotdata.append(futuredata)

            # if there is data from last year use that for the estimate
            elif year_old_data:
                logger.debug('last year estimate %s'%last_month)

                start = start_prediction_at
                period = 3600*24*30

                for a in range(0,12):
                    if level < 0:
                        break
                    data, level = getFutureData(start, period, level)
                    start += period
                    futuredata['data'] += data
                while len(futuredata['data']) > 0 and float(futuredata['data'][-1][1]) < 0:
                    del futuredata['data'][-1]
                try:
                    self.silo_days_left = str(int(((int(futuredata['data'][-1][0])/1000 - start_prediction_at) / (3600*24))))
                except Exception, e:
                    self.silo_days_left = '0'
                if level<= 0:
                    futuredata['data'] = decimateData(futuredata['data'], 50)
                    flotdata.append(futuredata)

            # otherwise estimate based on last month consumption with weighted monthly estimates
            else:
                if last_month == 0:
                    last_month = last_week * 4
                    logger.debug('last month estimate from last week * 4: %s'%last_month)

                if last_month > 0:
                    logger.debug('last month estimate %s'%last_month)
                    month_weights = (10,9,7,6,4,2,1,1,2,4,5,6)
                    now = datetime.today()
                    future = now
                    time_12h = timedelta(hours=12)
                    level = self.silo_level
                    t = start_prediction_at
                    while level > 0:
                        futuredata['data'].append([t*1000, level])
                        weighted_month = last_month / month_weights[now.month-1] * month_weights[future.month-1]
                        level = level - weighted_month / (28*2)
                        t += 12*3600
                        future += time_12h
                    self.silo_days_left = str(int((t - start_prediction_at) / (3600*24)))
                    futuredata['data'] = decimateData(futuredata['data'], 50)
                    flotdata.append(futuredata)
                else:
                     self.silo_days_left='365'

        except Exception, e:
            self.silo_days_left='0'
            logger.info('silolevel prediction error: %s'%str(e))

        self.siloData = {
            'graphdata':flotdata,
            'silo_level': self.silo_level,
            'silo_days_left': self.silo_days_left
        }
        self.updateTime=time.time()

        return json.dumps(self.siloData)


