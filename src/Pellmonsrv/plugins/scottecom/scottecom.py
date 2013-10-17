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
from Scotteprotocol import Protocol
import logging
import threading
from Pellmonsrv.plugin_categories import protocols
import menus
from descriptions import dataDescriptions

class scottecom(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, glob):
        print "scottecom"
        protocols.activate(self, glob)
        self.logger = logging.getLogger('yapsy')
        self.logger.info('starting scottecom plugin')
        self.conf.dbvalues={}

        # Initialize protocol and setup the database according to version_string
        try:
            self.protocol = Protocol(self.conf.serial_device, self.conf.version_string)
            self.allparameters = self.protocol.getDataBase()

            # Create and start settings_pollthread to log settings changed locally
            settings = menus.getDbWithTags(('Settings',))
            ht = threading.Timer(3, self.settings_pollthread, args=(settings,))
            ht.setDaemon(True)
            ht.start()

            # Create and start alarm_pollthread to log settings changed locally
            ht = threading.Timer(5, self.alarm_pollthread, args=(('mode', 'alarm'),))
            ht.setDaemon(True)
            ht.start()

            self.dataDescriptions = dataDescriptions
        except:
            self.logger.info('scottecom protocol setup failed')

    def getItem(self, item):
        return self.protocol.getItem(item)

    def setItem(self, item, value):
        return self.protocol.setItem(item, value)

    def getDataBase(self):
        db = self.protocol.getDataBase()
        return db.keys()

    def getDbWithTags(self, tags):
        """Get the menutags for param"""
        allparameters = self.getDataBase()
        filteredParams = menus.getDbWithTags(tags)            
        params = []
        for param in filteredParams:
            if param in allparameters:
                params.append(param)
        params.sort()
        return params

    def GetFullDB(self, tags):
        """Get list of all data/parameter/command items"""
        l=[]
        allparameters = self.protocol.getDataBase()
        filteredParams = self.getDbWithTags(tags)
        params = []
        for param in filteredParams:
            if param in allparameters:
                params.append(param)
        params.sort()
        for item in params:
            data={}
            data['name']=item
            if hasattr(allparameters[item], 'max'): 
                data['max']=(allparameters[item].max)
            if hasattr(allparameters[item], 'min'): 
                data['min']=(allparameters[item].min)
            if hasattr(allparameters[item], 'frame'): 
                if hasattr(allparameters[item], 'address'): 
                    data['type']=('R/W')
                else:
                    data['type']=('R')
            else:
                data['type']=('W')
            data['longname'] = dataDescriptions[item][0]
            data['unit'] = dataDescriptions[item][1]
            data['description'] = dataDescriptions[item][2]
            l.append(data)
        return l

    def settings_pollthread(self, settings):
        """Loop through all items tagged as 'Settings' and write a message to the log when their values have changed"""
        for item in settings:
            try:
                param = self.allparameters[item]
                value = self.protocol.getItem(item)
                if item in self.conf.dbvalues:
                    if not value==self.conf.dbvalues[item]:
                        log_change = True
                        # These are settings but their values are changed by the firmware also, 
                        # so small changes are suppressed from the log
                        selfmodifying_params = {'feeder_capacity': 25, 'feeder_low': 0.5, 'feeder_high': 0.8, 'time_minutes': 2, 'magazine_content': 1}
                        try:
                            change = abs(float(value) - float(self.conf.dbvalues[item]))
                            squelch = selfmodifying_params[item]
                            # These items change by themselves, log change only when squelch is exceeded
                            if change <= squelch:
                                log_change = False
                        except:
                            pass
                        # Don't log clock turn around
                        if (item == 'time_minutes' and change == 1439): 
                            log_change = False
                        if log_change:
                            self.settings_changed(item, self.conf.dbvalues[item], value)
                self.conf.dbvalues[item]=value
            except:
                pass
        # run this thread again after 30 seconds
        ht = threading.Timer(30, self.settings_pollthread, args=(settings,))
        ht.setDaemon(True)
        ht.start()

    def alarm_pollthread(self, alarms):
        # Log changes to 'mode' and 'alarm'
        for param in alarms:
            value = self.protocol.getItem(param)
            if param in self.conf.dbvalues:
                if not value==self.conf.dbvalues[param]:
                    self.settings_changed(param, self.conf.dbvalues[item], value)
            self.conf.dbvalues[param] = value
        # run this thread again after 30 seconds
        ht = threading.Timer(30, self.alarm_pollthread, args=(alarms,))
        ht.setDaemon(True)
        ht.start()

