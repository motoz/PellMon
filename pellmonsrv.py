#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import signal, os, Queue, threading, glib
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import logging
import logging.handlers
import sys
import ConfigParser
import time
from smtplib import SMTP as smtp
from email.mime.text import MIMEText as mimetext

from srv import Protocol, Daemon, getDbWithTags, dataDescriptions

class MyDBUSService(dbus.service.Object):
    """Publish an interface over the DBUS system bus"""
    def __init__(self):
        bus=dbus.SystemBus()
        bus_name = dbus.service.BusName('org.pellmon.int', bus)
        dbus.service.Object.__init__(self, bus_name, '/org/pellmon/int')

    @dbus.service.method('org.pellmon.int')
    def GetItem(self, param):
        """Get the value for a data/parameter item"""
        return protocol.getItem(param)

    @dbus.service.method('org.pellmon.int')
    def SetItem(self, param, value):
        """Get the value for a parameter/command item"""
        return protocol.setItem(param, value)

    @dbus.service.method('org.pellmon.int')
    def GetDB(self):
        """Get list of all data/parameter/command items"""
        l=[]
        dataBase = protocol.getDataBase()
        for item in dataBase:
            l.append(item)
        l.sort()
        if l==[]:
            return ['unsupported_version']
        else:
            return l

    @dbus.service.method(dbus_interface='org.pellmon.int', in_signature='as', out_signature='aa{sv}')
    def GetFullDB(self, tags):
        """Get list of all data/parameter/command items"""
        l=[]
        allparameters = protocol.getDataBase()
        filteredParams = getDbWithTags(tags)
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
        if l==[]:
            return ['unsupported_version']
        else:
            return l
                
    @dbus.service.method('org.pellmon.int')
    def GetDBwithTags(self, tags):
        """Get the menutags for param"""
        allparameters = protocol.getDataBase()
        filteredParams = getDbWithTags(tags)            
        params = []
        for param in filteredParams:
            if param in allparameters:
                params.append(param)
        params.sort()
        return params            
        
def pollThread():
    """Poll data defined in conf.pollData and update the RRD database with the responses"""
    logger.debug('handlerTread started by signal handler')
    items=[]
    global conf
    if not conf.polling:
        return
    try:
        for data in conf.pollData:
            # 'special cases' handled here, name starting with underscore are not polled from the protocol 
            if data[0]=='_':
                if data=='_logtick':
                    items.append(str(conf.tickcounter))
                else:
                    items.append('U')
            else:
                items.append(protocol.getItem(data))
        # Log changes to 'mode' and 'alarm' here, their data frame is already read here anyway
        for param in ('mode', 'alarm'):
            value = protocol.getItem(param)
            if param in conf.dbvalues:
                if not value==conf.dbvalues[param]:
                    logline='%s changed from %s to %s'%(param, conf.dbvalues[param], value)
                    logger.info(logline)
                    conf.tickcounter=int(time.time())
                    if conf.email and param in conf.emailconditions:
                        sendmail(logline)
                    for data in conf.pollData:
                        if data=='_logtick':
                            items.append(str(conf.tickcounter))
            conf.dbvalues[param] = value
        s=':'.join(items)
        os.system("/usr/bin/rrdtool update "+conf.db+" N:"+s)
    except IOError as e:
        logger.debug('IOError: '+e.strerror)
        logger.debug('   Trying Z01...')
        try:
            # I have no idea why, but every now and then the pelletburner stops answering, and this somehow causes it to start responding normally again
            protocol.getItem('oxygen_regulation')
        except IOError as e:
            logger.info('Getitem failed two times and reading Z01 also failed '+e.strerror)
    

def periodic_signal_handler(signum, frame):
    """Periodic signal handler. Start pollThread to do the work"""
    ht = threading.Thread(name='pollThread', target=pollThread)
    ht.setDaemon(True)
    ht.start()

def copy_db(direction='store'):
    """Copy db to nvdb or nvdb to db depending on direction"""
    global copy_in_progress
    if not 'copy_in_progress' in globals():
        copy_in_progress = False        
    if not copy_in_progress:
        if direction=='store':
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(conf.db, conf.nvdb)) 
                logger.debug('copied %s to %s'%(conf.db, conf.nvdb))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(conf.db, conf.nvdb))
            finally:
                copy_in_progress = False
        else:
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(conf.nvdb, conf.db))  
                logger.info('copied %s to %s'%(conf.nvdb, conf.db))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(conf.nvdb, conf.db))
            finally:
                copy_in_progress = False
    
def db_copy_thread():
    """Run periodically at db_store_interval to call copy_db""" 
    copy_db('store')    
    ht = threading.Timer(conf.db_store_interval, db_copy_thread)
    ht.setDaemon(True)
    ht.start()

def sigterm_handler(signum, frame):
    """Handles SIGTERM, waits for the database copy on shutdown if it is in a ramdisk"""
    if conf.polling: 
        if conf.nvdb != conf.db:   
            copy_db('store')
        if not copy_in_progress:
            logger.info('exiting')
            sys.exit(0)
    else:
        logger.info('exiting')
        sys.exit(0)
    
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
                                selfmodifying_params = {'feeder_capacity': 25, 'feeder_low': 0.5, 'feeder_high': 0.8, 'time_minutes': 2}
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

def sendmail(msg):
    ht = threading.Timer(2, sendmail_thread, args=(msg,))
    ht.start()

def sendmail_thread(msg):
    try:
        username = conf.emailusername 
        password = conf.emailpassword
        
        mail = mimetext(msg)
        mail['Subject'] = conf.emailsubject
        mail['From'] = conf.emailfromaddress
        mail['To'] = conf.emailtoaddress

        mailserver = smtp(conf.emailserver)
        mailserver.starttls() 
        mailserver.login(conf.emailusername, conf.emailpassword)  
        mailserver.sendmail(mail['From'], mail['To'], mail.as_string())      
        mailserver.quit()  
    except:
        logger.info('error trying to send email')
    
class MyDaemon(Daemon):
    """ Run after double fork with start, or directly with debug argument"""
    def run(self):
    
        # Init global configuration from the conf file
        global conf
        conf = config(config_file)

        global logger
        logger = logging.getLogger('pellMon')

        logger.info('starting pelletMonitor')

        # Initialize protocol and setup the database according to version_string
        global protocol 
        protocol = Protocol(conf.serial_device, conf.version_string)
        
        # DBUS needs the gobject main loop, this way it seems to work...
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()    
        DBUSMAINLOOP = gobject.MainLoop()
        DBusGMainLoop(set_as_default=True)
        myservice = MyDBUSService()
        
        # Create SIGTERM signal handler
        signal.signal(signal.SIGTERM, sigterm_handler)

        # Create poll_interval periodic signal handler
        signal.signal(signal.SIGALRM, periodic_signal_handler)
        logger.debug('created signalhandler')
        signal.setitimer(signal.ITIMER_REAL, 2, conf.poll_interval)
        logger.debug('started timer')
        
        # Create RRD database if does not exist
        if conf.polling:
            if not os.path.exists(conf.nvdb):
                os.system(conf.RrdCreateString)
                logger.info('Created rrd database: '+conf.RrdCreateString)

            # If nvdb is different from db, copy nvdb to db
            if conf.nvdb != conf.db:
                copy_db('restore')
                # Create and start db_copy_thread to store db at regular interval
                ht = threading.Timer(conf.db_store_interval, db_copy_thread)
                ht.setDaemon(True)
                ht.start()

        # Create and start settings_pollthread to log settings changed locally
        settings = getDbWithTags(('Settings',))        
        ht = threading.Timer(4, settings_pollthread, args=(settings,))
        ht.setDaemon(True)
        ht.start()
       
        # Execute glib main loop to serve DBUS connections
        DBUSMAINLOOP.run()
        
        # glib main loop has quit, this should not happen
        logger.info("ending, what??")
        
class config:
    """Contains global configuration, parsed from the .conf file"""
    def __init__(self, filename):
        # Load the configuration file
        parser = ConfigParser.ConfigParser()
        parser.read(filename)
    
        # These are read from the serial bus every 'pollinterval' second
        polldata = parser.items("pollvalues")

        # Optional rrd data source definitions, default is DS:%s:GAUGE:%u:U:U
        rrd_datasources = parser.items("rrd_datasources")

        self.pollData = []
        self.dataSources = {}
        dataSourceConf = {}
        for key, value in rrd_datasources:
            dataSourceConf[key] = value
        for key, value in polldata:
            self.pollData.append(value)
            if dataSourceConf.has_key(key):
                self.dataSources[value] = dataSourceConf[key]
            else:
                self.dataSources[value] = "DS:%s:GAUGE:%u:U:U"
        # The RRD database
        try:
            self.polling=True
            self.db = parser.get('conf', 'database')
        except ConfigParser.NoOptionError:
            self.polling=False

        # The persistent RRD database
        try:
            self.nvdb = parser.get('conf', 'persistent_db') 
        except ConfigParser.NoOptionError:
            if self.polling:
                self.nvdb = self.db        
        try:
            self.db_store_interval = int(parser.get('conf', 'db_store_interval'))
        except ConfigParser.NoOptionError:
            self.db_store_interval = 3600
        try:
            self.serial_device = parser.get('conf', 'serialport') 
        except ConfigParser.NoOptionError:
            self.serial_device = None
        try:
            self.version_string = parser.get('conf', 'chipversion')
        except ConfigParser.NoOptionError:
            logger.info('chipversion not specified, using 0.0')
            self.version_string = '0.0'
        try: 
            self.poll_interval = int(parser.get('conf', 'pollinterval'))
        except ConfigParser.NoOptionError:
            logger.info('Invalid poll_interval setting, using 10s')
            self.poll_interval = 10

        if self.polling:
            # Build a command string to create the rrd database
            self.RrdCreateString="rrdtool create %s --step %u "%(self.nvdb, self.poll_interval)
            for item in self.pollData:
                self.RrdCreateString += self.dataSources[item] % (item, self.poll_interval*4) + ' ' 
            self.RrdCreateString += "RRA:AVERAGE:0,999:1:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:10:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:100:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:1000:20000" 

        # create logger
        logger = logging.getLogger('pellMon')
        loglevel = parser.get('conf', 'loglevel')
        loglevels = {'info':logging.INFO, 'debug':logging.DEBUG}
        try:
            logger.setLevel(loglevels[loglevel])
        except:
            logger.setLevel(logging.DEBUG)
        # create file handler for logger
        fh = logging.handlers.WatchedFileHandler(parser.get('conf', 'logfile'))
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        
        # dict to hold known recent values of db items
        self.dbvalues = {} 

        # count every parameter and mode change so rrd can draw a tick mark when that happens
        self.tickcounter = int(time.time())
        
        try:
            self.emailusername = parser.get('email', 'username')
            self.emailpassword = parser.get('email', 'password')
            self.emailfromaddress = parser.get('email', 'from')
            self.emailtoaddress = parser.get('email', 'to')
            self.emailsubject = parser.get('email', 'subject')
            self.emailserver = parser.get('email', 'server')
            self.emailconditions = parser.get('email', 'conditions')
            self.email=True
        except ConfigParser.NoOptionError:
            self.email=False
            
#########################################################################################



if __name__ == "__main__":
  
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pellmon.conf')
    
    daemon = MyDaemon('/tmp/pelletMonitor.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'debug' == sys.argv[1]:
            daemon.run()
        else:
            print "Unknown command"
            sys.exit(2)
            sys.exit(0)
    else:
        print "usage: %s start|stop|restart|debug" % sys.argv[0]
        sys.exit(2)



