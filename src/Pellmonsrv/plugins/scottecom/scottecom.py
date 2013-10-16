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
from menus import getDbWithTags
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
            settings = getDbWithTags(('Settings',))
            ht = threading.Timer(4, self.settings_pollthread, args=(settings,))
            ht.setDaemon(True)
            ht.start()
            self.dataDescriptions = dataDescriptions
        except:
            self.logger.info('scottecom protocol setup failed')

    def getDbWithTags(self, tags):
        return getDbWithTags(tags)

    def settings_pollthread(self, settings):
        """Loop through all items tagged as 'Settings' and write a message to the log when their values have changed"""
        for item in settings:
            try:
                param = self.allparameters[item]
                paramrange = param.max - param.min
                value = self.protocol.getItem(item)
                if item in self.conf.dbvalues:
                    logline=''
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
                            logline = 'Parameter %s changed from %s to %s'%(item, self.conf.dbvalues[item], value)
                            logger.info(logline)
                            self.conf.tickcounter=int(time.time())
                        self.conf.dbvalues[item]=value
                        if logline and self.conf.email and 'parameter' in self.conf.emailconditions:
                            self.sendmail(logline)
                else:
                    self.conf.dbvalues[item]=value
            except:
                pass
        # run this thread again after 30 seconds
        ht = threading.Timer(30, self.settings_pollthread, args=(settings,))
        ht.setDaemon(True)
        ht.start()
