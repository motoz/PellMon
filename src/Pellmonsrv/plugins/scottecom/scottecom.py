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
from Pellmonsrv.database import Item, Getsetitem
import menus
from descriptions import dataDescriptions

class scottecom(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db):
        protocols.activate(self, conf, glob, db)
        self.logger = logging.getLogger('pellMon')
        self.dbvalues={}
        self.itemrefs = []

        # Initialize protocol and setup the database according to version_string
        try:
            try:
                self.protocol = Protocol(self.conf['serialport'], self.conf['chipversion'])
            except:
                # Create testprotocol if conf is missing
                self.protocol = Protocol(None, '')
            self.allparameters = self.protocol.getDataBase()

            """Get list of all data/parameter/command items"""
            params = self.protocol.getDataBase()
            for item in params:
                dbitem = Getsetitem(item, lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
                if hasattr(params[item], 'max'): 
                    dbitem.max = str(params[item].max)
                if hasattr(params[item], 'min'): 
                    dbitem.min = str(params[item].min)
                if hasattr(params[item], 'frame'): 
                    if hasattr(params[item], 'address'): 
                        dbitem.type = 'R/W'
                    else:
                        dbitem.type = 'R'
                else:
                    dbitem.type = 'W'
                dbitem.longname = dataDescriptions[item][0]
                dbitem.unit = dataDescriptions[item][1]
                dbitem.description = dataDescriptions[item][2]
                dbitem.tags = menus.itemtags(item)
                self.db.insert(dbitem)
                self.itemrefs.append(dbitem)

            # Create and start settings_pollthread to log settings changed locally
            settings = [item for item in params if 'Settings' in menus.itemtags(item)]
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

    def getItem(self, item, raw=False):
        return self.protocol.getItem(item, raw)

    def setItem(self, item, value, raw=False):
        return self.protocol.setItem(item, value, raw)

    def getDataBase(self):
        db = self.protocol.getDataBase()
        return db.keys()

    def getMenutags(self):
        return menus.getMenutags()

    def settings_pollthread(self, settings):
        """Loop through all items tagged as 'Settings' and write a message to the log when their values have changed"""
        for item in settings:
            try:
                param = self.allparameters[item]
                value = self.protocol.getItem(item, raw=True)
                if item in self.dbvalues:
                    if not value==self.dbvalues[item]:
                        log_change = True
                        # These are settings but their values are changed by the firmware also, 
                        # so small changes are suppressed from the log
                        selfmodifying_params = {'feeder_capacity': 25, 'feeder_low': 0.5, 'feeder_high': 0.8, 'time_minutes': 3, 'magazine_content': 1}
                        try:
                            change = abs(float(value) - float(self.dbvalues[item]))
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
                            self.settings_changed(item, self.dbvalues[item], value)
                self.dbvalues[item]=value
            except:
                pass
        # run this thread again after 30 seconds
        ht = threading.Timer(30, self.settings_pollthread, args=(settings,))
        ht.setDaemon(True)
        ht.start()

    def alarm_pollthread(self, alarms):
        # Log changes to 'mode' and 'alarm'
        try:
            for param in alarms:
                value = self.protocol.getItem(param)
                if param in self.dbvalues:
                    if not value==self.dbvalues[param]:
                        self.settings_changed(param, self.dbvalues[param], value, param)
                self.dbvalues[param] = value
        except:
            pass
        # run this thread again after 30 seconds
        ht = threading.Timer(30, self.alarm_pollthread, args=(alarms,))
        ht.setDaemon(True)
        ht.start()

