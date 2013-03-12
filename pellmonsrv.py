#! /usr/bin/python
# -*- coding: iso-8859-15 -*-
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

import signal, os, time, Queue, serial, socket, threading, glib
from datetime import datetime
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import exceptions
import logging
import logging.handlers
import sys
import ConfigParser
from threading import Lock
import serial
from srv import *

# Publish an interface over the DBUS system bus
class MyDBUSService(dbus.service.Object):
    def __init__(self):
        bus=dbus.SystemBus()
        bus_name = dbus.service.BusName('org.pellmon.int', bus)
        dbus.service.Object.__init__(self, bus_name, '/org/pellmon/int')

    @dbus.service.method('org.pellmon.int')
    def GetItem(self, param):
        return getItem(param)

    @dbus.service.method('org.pellmon.int')
    def SetItem(self, param, value):
        return setItem(param, value)

    @dbus.service.method('org.pellmon.int')
    def GetDB(self):
        l=[]
        dataBase = getDataBase()
        for item in dataBase:
            l.append(item)
        l.sort()
        if l==[]:
            return ['unsupported_version']
        else:
            return l

# Poll data and update the RRD database
def handlerThread():
        logger.debug('handlerTread started by signal handler')
        items=[]
        try:
            for data in pollData:
                items.append(getItem(data))
            s=':'.join(items)
            os.system("/usr/bin/rrdtool update "+db+" N:"+s)
            #logger.setLevel(logging.INFO)
        except IOError as e:
            #logger.setLevel(logging.DEBUG)
            logger.info('IOError: '+e.strerror)
            logger.info('   Trying Z01...')
            try:
                # I have no idea why, but every now and then the pelletburner stops answering, and this somehow causes it to start responding normally again
                getItem('oxygen_regulation')
            except IOError as e:
                logger.info('      failed '+e.strerror)

# Signal handler start handlerThread at regular interval
def handler(signum, frame):
    ht = threading.Thread(name='poll_thread', target=handlerThread)
    ht.setDaemon(True)
    ht.start()

copy_in_progress = False

def copy_db(direction='store'):
    global copy_in_progress
    if not copy_in_progress:
        if direction=='store':
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(db, nvdb)) 
                logger.info('copied %s to %s'%(db, nvdb))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(db, nvdb))
            finally:
                copy_in_progress = False
        else:
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(nvdb, db))  
                logger.info('copied %s to %s'%(nvdb, db))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(nvdb, db))
            finally:
                copy_in_progress = False
    
def db_copy_thread():
    copy_db('store')    
    ht = threading.Timer(db_store_interval, db_copy_thread)
    ht.setDaemon(True)
    ht.start()

def sigterm_handler(signum, frame):
    if nvdb != db:   
        copy_db('store')
    if not copy_in_progress:
        logger.info('exiting')
        sys.exit(0)
    
class MyDaemon(Daemon):
    def run(self):
        create_globals()
        
        # DBUS needs the gobject main loop, this way it seems to work...
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()    
        DBUSMAINLOOP = gobject.MainLoop()
        DBusGMainLoop(set_as_default=True)
        myservice = MyDBUSService()
        
        initProtocol(ser, version_string)
        
        logger.info('starting pelletMonitor')
        
        # Create SIGTERM signal handler
        signal.signal(signal.SIGTERM, sigterm_handler)

        # Create poll_interval periodic signal handler
        signal.signal(signal.SIGALRM, handler)
        logger.info('created signalhandler')
        signal.setitimer(signal.ITIMER_REAL, 2, poll_interval)
        logger.info('started timer')
        
        # Create RRD database, if nvdb defined copy it to db
        if nvdb != db:
            if not os.path.exists(nvdb):
                os.system(RrdCreateString)
                logger.info('Created rrd database: '+RrdCreateString)
            copy_db('restore')
            # Create and start db_copy_thread to store db at regular interval
            #ht = threading.Thread(name='db_copy_thread', target=db_copy_thread)
            ht = threading.Timer(db_store_interval, db_copy_thread)
            ht.setDaemon(True)
            ht.start()
        else:
            if not os.path.exists(db):
                os.system(RrdCreateString)
                logger.info('Created rrd database: '+RrdCreateString)
       
        # Execute glib main loop to serve DBUS connections
        DBUSMAINLOOP.run()
        
        # glib main loop has quit
        logger.info("end")

# Create global stuff
def create_globals():
    global parser
    parser = ConfigParser.ConfigParser()

    # Load the configuration file
    parser.read(config_file)

    # These are read from the serial bus every 'pollinterval' second
    polldata = parser.items("pollvalues")

    # Optional rrd data source definitions, default is DS:%s:GAUGE:%u:U:U
    rrd_datasources = parser.items("rrd_datasources")

    global pollData
    pollData = []
    global dataSources
    dataSources = {}
    dataSourceConf = {}
    for key, value in rrd_datasources:
        dataSourceConf[key] = value
    for key, value in polldata:
        pollData.append(value)
        if dataSourceConf.has_key(key):
            dataSources[value] = dataSourceConf[key]
        else:
            dataSources[value] = "DS:%s:GAUGE:%u:U:U"

    global db    
    # The RRD database
    db = parser.get('conf', 'database') 

    # The persistent RRD database
    try:
        global nvdb
        nvdb = parser.get('conf', 'persistent_db') 
    except:
        nvdb = db        
    try:
        global db_store_interval
        db_store_interval = int(parser.get('conf', 'db_store_interval'))
    except:
        db_store_interval = 3600        

    # create logger
    global logger
    logger = logging.getLogger('pellMon')
    loglevel = parser.get('conf', 'loglevel')
    loglevels = {'info':logging.INFO, 'debug':logging.DEBUG}
    try:
        logger.setLevel(loglevels[loglevel])
    except:
        logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.handlers.WatchedFileHandler(parser.get('conf', 'logfile'))
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.info('loglevel: '+loglevel)

    # Open serial port
    global ser
    ser = serial.Serial()
    ser.port     = parser.get('conf', 'serialport') 
    ser.baudrate = 9600
    ser.parity   = 'N'
    ser.rtscts   = False
    ser.xonxoff  = False
    ser.timeout  = 1        
    try:
        ser.open()
    except serial.SerialException, e:
        logger.info("Could not open serial port %s: %s\n" % (ser.portstr, e))
    logger.info('serial port ok')

    global version_string
    version_string = parser.get('conf', 'chipversion')

    if version_string == None:
        version_string = '0.0'

    logger.info('Chip version: %s'%version_string)    

    try: 
        global poll_interval
        poll_interval = int(parser.get('conf', 'pollinterval'))
    except:
        poll_interval = 10
        logger.info('invalid poll interval setting, using 10s')

    # Build a command string to create the rrd database
    global RrdCreateString
    RrdCreateString="rrdtool create %s --step %u "%(nvdb, poll_interval)
    for item in pollData:
        RrdCreateString=RrdCreateString + dataSources[item] % (item, poll_interval*4) + ' ' 
    RrdCreateString=RrdCreateString+"RRA:AVERAGE:0,999:1:20000 " 
    RrdCreateString=RrdCreateString+"RRA:AVERAGE:0,999:10:20000 " 
    RrdCreateString=RrdCreateString+"RRA:AVERAGE:0,999:100:20000 " 
    RrdCreateString=RrdCreateString+"RRA:AVERAGE:0,999:1000:20000" 

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



