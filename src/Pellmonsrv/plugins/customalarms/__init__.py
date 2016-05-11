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
from Pellmonsrv.database import Item, Getsetitem
from threading import Thread, Timer
from os import path
import os, grp, pwd
from logging import getLogger

logger = getLogger('pellMon')

itemList=[]
itemTags={}
itemValues={}
Menutags = ['CustomAlarms']
alarms = {}

class alarmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        for key, value in self.conf.iteritems():
            try:
                alarm_name = key.split('_')[0]
                alarm_data = key.split('_')[1]
                if alarm_data == 'status':
                    alarm_type = 'R'
                    description = 'The name of the parameter that has the status for this alarm'
                elif alarm_data == 'comparator':
                    alarm_type = 'R/W'
                    description = 'Allowed values: >|>=|<|<=|==|!='
                elif alarm_data == 'level':
                    alarm_type = 'R/W'
                    description = 'compare against this value'
                elif alarm_data == 'item':
                    alarm_type = 'R/W'
                    description = 'Parameter to read from'
                elif alarm_data == 'enum':
                    alarm_type = 'R/W'
                    description = 'set to: alarm OFF text|alarm ON text'

                itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'', 'type':alarm_type, 'description':description})
                itemTags[key] = ['All', 'CustomAlarms', 'Basic']

                if not alarms.has_key(alarm_name):
                    alarms[alarm_name] = {}
                alarm_data = key.split('_')[1]
                if alarm_data == 'status':
                    itemList.append({'name':value, 'value':0, 'unit':'', 'type':'R', 'description':'%s status'%alarm_name})
                    itemTags[value] = ['All', 'CustomAlarms', 'Basic']

                if alarm_data in ['item','comparator','level','status']:
                    if not alarms.has_key(alarm_name):
                        alarms[alarm_name] = {}
                    alarms[alarm_name][alarm_data] = value
            except Exception,e:
                logger.info(str(e))
            itemTags[key].append(alarm_name)

        self.migrate_settings('customalarms')

        for item in itemList:
            if item['type'] == 'R/W':
                self.store_setting(item['name'], confval = item['value'])
                value = self.load_setting(item['name'])
            else:
                value = item['value']
                itemValues[item['name']] = value

            dbitem = Getsetitem(item['name'], value, lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
            for key, value in item.iteritems():
                if key is not 'value':
                    dbitem.__setattr__(key, value)
            if dbitem.name in itemTags:
                dbitem.__setattr__('tags', itemTags[dbitem.name])
            self.db.insert(dbitem)
            self.itemrefs.append(dbitem)

        t = Timer(5, self.poll_thread)
        t.setDaemon(True)
        t.start()

    def getItem(self, item):
        try:
            return str(itemValues[item])
        except:
            try:
                return self.load_setting(item)
            except:
                return 'error'

    def setItem(self, item, value):
        try:
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                self.store_setting(item, value)
                return 'OK'
        except Exception,e:
            return 'error'

    def getMenutags(self):
        return Menutags

    def poll_thread(self):
        for name, data in alarms.items():
            try:
                item = self.getItem(name+'_item')
                value = float(self.db[item].value)
                comparator = self.getItem(name+'_comparator')
                level = float(self.getItem(name+'_level'))
                alarm = 0
                if comparator == '<':
                    if value < level:
                        alarm = 1
                elif comparator == '<=':
                    if value <= level:
                        alarm = 1
                elif comparator == '>':
                    if value > level:
                        alarm = 1
                elif comparator == '>=':
                    if value >= level:
                        alarm = 1
                elif comparator == '==':
                    if value == level:
                        alarm = 1
                elif comparator == '!=':
                    if value != level:
                        alarm = 1
                status_item = self.getItem(name+'_status')
                oldState  = self.getItem(status_item)
                if str(alarm) != oldState:
                    self.setItem(status_item, alarm)
                    try:
                        enum = self.getItem(name+'_enum').split('|')
                        if alarm:
                            self.settings_changed(name, enum[0], enum[1], 'alarm')
                        else:
                            self.settings_changed(name, enum[1], enum[0], 'alarm')
                    except:
                        self.settings_changed(name, oldState, alarm, 'alarm')
            except:
                pass
        t = Timer(5, self.poll_thread)
        t.setDaemon(True)
        t.start()
