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
from Scotteprotocol import Protocol, getDbWithTags, dataDescriptions
import logging
import threading
from Pellmonsrv.plugin_categories import protocols

class scottecom(protocols):
    def setup(self, conf):
        print "scottecom"
        self.conf = conf

        self.logger = logging.getLogger('yapsy')

        self.logger.info('starting scottecom plugin')

        # Initialize protocol and setup the database according to version_string
        try:
            self.protocol = Protocol(self.conf.serial_device, self.conf.version_string)
        except:
            self.conf.polling=False
            logger.info('scottecom protocol setup failed')

        # Create and start settings_pollthread to log settings changed locally
        settings = getDbWithTags(('Settings',))        
        ht = threading.Timer(4, settings_pollthread, args=(settings,))
        ht.setDaemon(True)
        ht.start()

def settings_pollthread(settings):
    """Loop through all items tagged as 'Settings' and write a message to the log when their values have changed"""
    global conf
    allparameters = protocol.getDataBase()    
    for item in settings:
        if item in allparameters:
            param = allparameters[item]
            if hasattr(param, 'max') and hasattr(param, 'min') and hasattr(param, 'frame'):
                paramrange = param.max - param.min
                try:
                    value = protocol.getItem(item)
                    if item in conf.dbvalues:
                        try:
                            logline=''
                            if not value==conf.dbvalues[item]:
                                # These are settings but their values are changed by the firmware also, 
                                # so small changes are suppressed from the log
                                selfmodifying_params = {'feeder_capacity': 25, 'feeder_low': 0.5, 'feeder_high': 0.8, 'time_minutes': 2, 'magazine_content': 1}
                                try:
                                    change = abs(float(value) - float(conf.dbvalues[item]))
                                    squelch = selfmodifying_params[item]
                                    # These items change by themselves, log change only if bigger than 0.3% of range
                                    if change > squelch:
                                        # Don't log clock turn around
                                        if not (item == 'time_minutes' and change == 1439): 
                                            logline = 'Parameter %s changed from %s to %s'%(item, conf.dbvalues[item], value)
                                            logger.info(logline)
                                            conf.tickcounter=int(time.time())
                                except:
                                    logline = 'Parameter %s changed from %s to %s'%(item, conf.dbvalues[item], value)
                                    logger.info(logline)
                                    conf.tickcounter=int(time.time())
                                conf.dbvalues[item]=value
                                if logline and conf.email and 'parameter' in conf.emailconditions:
                                    sendmail(logline)
                        except:
                            logger.info('trouble with parameter change detection, item:%s'%item)
                    else:
                        conf.dbvalues[item]=value        
                except:
                    pass
    # run this thread again after 30 seconds        
    ht = threading.Timer(30, settings_pollthread, args=(settings,))
    ht.setDaemon(True)
    ht.start()
