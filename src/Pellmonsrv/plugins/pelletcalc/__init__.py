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
from logging import getLogger
import traceback

logger = getLogger('pellMon')

itemList=[
          {'name':'feeder_capacity',      'longname':'feeder 6 min capacity',    'type':'R/W', 'unit':'g/360s', 'value': '1000', 'min':'0', 'max':'5000' },
          {'name':'feeder_time',          'longname':'feeder time',              'type':'R',   'unit':'s',      'value': '0'    },
          {'name':'power_kW',             'longname':'power',                    'type':'R',   'unit':'kW',     'value': '0'    }, 
          {'name':'mode',                 'longname':'mode',                     'type':'R',   'unit':'',       'value': '-'  }, 
          {'name':'alarm',                'longname':'alarm',                    'type':'R',   'unit':'',       'value': '-'  }, 
         ]

counter_mode_items = [
        {'name':'feeder_rev_capacity',  'longname':'feeder capacity',          'type':'R',   'unit':'g'   ,   'value': '5.56' },
        {'name':'feeder_rpm',           'longname':'feeder rpm',               'type':'R',   'unit':'/60s',   'value': '30'   },
        {'name':'feeder_rp6m',          'longname':'feeder rev per 6 min',     'type':'R/W', 'unit':'/360s',  'value': '180',  'min':'0', 'max':'500'  },
          
        {'name':'feeder_rev',           'longname':'feeder rev count',         'type':'R',   'unit':' ',      'value': '',    'min':'0', 'max':'-'    },
]

itemTags = {'feeder_capacity' :     ['All', 'pelletCalc', 'Basic'],
            'feeder_time' :         ['All', 'pelletCalc'],
            'power_kW' :            ['All', 'pelletCalc', 'Basic', 'Overview'],
            'mode' :                ['All', 'pelletCalc', 'Basic', 'Overview'],
            'alarm' :               ['All', 'pelletCalc', 'Basic', 'Overview'],
           }

counter_mode_tags = {
        'feeder_rev_capacity' : ['All', 'pelletCalc'],
        'feeder_rpm' :          ['All', 'pelletCalc'],
        'feeder_rp6m' :         ['All', 'pelletCalc', 'Basic'],
        'feeder_rev' :          ['All', 'pelletCalc', 'Basic'],
}

itemDescriptions = {'feeder_rev_capacity' : 'Average grams fed in one revolution',
                    'feeder_rpm' :          'Feeder screw rotation speed',
                    'feeder_capacity' :     'Grams fed in 360 seconds',
                    'feeder_rp6m' :         'Feeder screw revolutions in 360 seconds',
                    'feeder_rev' :          'Feeder screw revolutions count',
                    'feeder_time' :         'Feeder screw run time',
                    'power_kW' :            'Power calculated from fed pellet mass/time',
                    'mode' :                'Current burner state',
                    'alarm' :               'Current burner alarm state',
                    }

Menutags = ['pelletCalc', 'Overview']


class pelletcalc(protocols):
    def __init__(self):
        protocols.__init__(self)
        self.power = 0
        self.state = 'Off'
        self.oldstate = self.state
        self.time_count = time()
        self.time_state = self.time_count
        self.feeder_time = None
        self.alarm_state = 'OK'

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        if not 'timer' in conf:
            global itemList
            itemList += counter_mode_items
            itemTags.update(counter_mode_tags)
        self.valuestore = ConfigParser()
        self.valuestore.add_section('values')
        self.valuesfile = path.join(path.dirname(__file__), 'values.conf')
        for item in itemList:
            if item['type'] == 'R/W':
                self.valuestore.set('values', item['name'], str(item['value']))
        self.valuestore.read(self.valuesfile)

        try:
            uid = pwd.getpwnam(self.glob['conf'].USER).pw_uid
            gid = grp.getgrnam(self.glob['conf'].GROUP).gr_gid
            os.chown(self.valuesfile, uid, gid)
        except:
            pass

        with open(self.valuesfile, 'w') as f:
            self.valuestore.write(f)

        t = Timer(5, self.calc_thread)
        t.setDaemon(True)
        t.start()

    def deactivate(self):
        protocols.deactivate(self)

    def getItem(self, item):
        if item == 'feeder_rev':
            return self.getGlobalItem(self.conf['counter'])
        elif item == 'feeder_time':
            if 'timer' in self.conf:
                return str(int(round(float(self.getGlobalItem(self.conf['timer'])))))
            else:
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
        elif item == 'mode':
            return self.state
        elif item == 'alarm':
            return self.alarm_state
        else:
            for i in itemList:
                if i['name'] == item:
                    if i['type'] == 'R/W':
                        return str(self.valuestore.get('values', item))
                    else:
                        return i['value']
        return 'Error'

    def setItem(self, item, value):
        for i in itemList:
            if i['name'] == item:
                i['value'] = value
                if i['type'] in['R/W', 'W']:
                    self.valuestore.set('values', item, str(value))
                    with open(self.valuesfile, 'w') as f:
                        self.valuestore.write(f)
                return 'OK'
        return 'Error'

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


    def calculate_state(self):
        try:
            feeder_time = float(self.getItem('feeder_time'))
            if self.feeder_time == None:
                 self.feeder_time = feeder_time
            power = float(self.getItem('power_kW'))
        except Exception,e:
            return
        if self.state in ('Off', 'Ignition failed'):
            if feeder_time > self.feeder_time:
                # switch to 'Starting' as soon as some feeder activity is detected
                self.feeder_time = feeder_time
                self.time_feeder_time = time()
                self.time_state = self.time_feeder_time
                self.state = 'Starting'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state
                if not self.alarm_state == 'OK':
                    self.settings_changed('alarm', self.alarm_state, 'OK', itemtype='alarm')
                    self.alarm_state = 'OK'

        elif self.state == 'Starting':
            if feeder_time > self.feeder_time:
                self.feeder_time = feeder_time
                self.time_feeder_time = time()
            if time() - self.time_state > 60:
                # switch to 'Igniting' after 60s
                self.time_state = time()
                self.state = 'Igniting'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state

        elif self.state == 'Igniting':
            if feeder_time > self.feeder_time:
                self.feeder_time = feeder_time
                self.time_feeder_time = time()
            if time() - self.time_feeder_time > 600:
                # if we are still in 'Igniting' after 10 min then go to 'Ignition failed'
                self.time_state = time()
                self.state = 'Ignition failed'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state
                self.alarm_state = 'Ignition failed'
                self.settings_changed('alarm', 'OK', self.alarm_state, itemtype='alarm')
            if power > 5:
                # switch to 'Running' when the 5 min average power is above 5kW
                self.time_state = time()
                self.state = 'Running'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state

        elif self.state == 'Ignition failed':
            # Getting out of here is handled by the 'Off' case
            pass

        elif self.state == 'Running':
            if feeder_time > self.feeder_time:
                self.feeder_time = feeder_time
                self.time_feeder_time = time()
            if time() - self.time_feeder_time > 60:
                # No activity for 60s, got to 'Cooling'
                self.time_state = time()
                self.state = 'Cooling'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state

        elif self.state == 'Cooling':
            if feeder_time > self.feeder_time:
                # apparently it didn't shut down, go back to 'Running'
                self.feeder_time = feeder_time
                self.time_feeder_time = time()
                self.time_state = time()
                self.state = 'Running'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state
            elif power < 0.1:
                # stay here until 5min average power is below 0.1kW
                self.time_state = time()
                self.state = 'Off'
                self.settings_changed('mode', self.oldstate, self.state, itemtype='mode')
                self.oldstate = self.state


    def calc_thread(self):
        """ Calculate last 5 minutes mean power """
        timelist = []

        try:
            last_timer = int(self.getItem('feeder_time'))
            last_time = time()
            last_state = self.state
            timer_sum = 0
            timelist.append( (last_timer, last_time, last_state) )
            sleep(5)
            while True:
                try:
                    timer = int(self.getItem('feeder_time'))
                    now = time()
                    timelist.append( (timer, now, self.state) )
                    if timer > last_timer:
                        if self.state in ('Igniting','Running','Cooling'):
                            timer_sum += (timer - last_timer)
                    if now - timelist[0][1] > 300 and len(timelist)>1:
                        if timelist[1][2] in ('Igniting','Running','Cooling'):
                            timer_sum -= (timelist[1][0] - timelist[0][0])
                        del timelist[0]

                    last_timer = timer
                    last_time = now

                    try:
                        capacity = float(self.getItem('feeder_capacity')) / 360
                        self.power = timer_sum * capacity * 12 * 4.8 * 0.9 / 1000
                        self.calculate_state()
                    except KeyError:
                        logger.info("PelletCalc error, can't read 'feeder_capacity'")
                except Exception, e:
                    pass
                sleep(5)
        except KeyError:
            logger.info("PelletCalc error, can't read 'feeder_time'")
