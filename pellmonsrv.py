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
from daemon import Daemon
import sys
from collections import namedtuple
import ConfigParser
from threading import Lock
import serial

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
        for item in dataBase:
            l.append(item)
        l.sort()
        if l==[]:
            return ['unsupported_version']
        else:
            return l

def addCheckSum(s):
    x=0;
    logger.debug('addchecksum:')
    for c in s: x=x^ord(c)
    rs=s+chr(x)
    logger.debug(rs)
    return rs

def checkCheckSum(s):
    x=0;
    for c in s: 
        x=x^ord(c)
    return x
        
def pollThread():
    while True:  
        commandqueue = q.get() 

        # Write parameter/command       
        if commandqueue[0]==2:
            s=addCheckSum(commandqueue[1])
            logger.debug('serial write'+s)
            ser.write(s+'\r')   
            logger.debug('serial written'+s)        
            line=""
            ser.flushInput()
            try:
                line=str(ser.read(3))
                logger.debug('serial read'+line)
            except: 
                logger.debug('Serial read error')
            if line:
                # Send back the response
                commandqueue[2].put(line)
            else:
                commandqueue[2].put("No answer")
                logger.info('No answer')
        
        # Get frame command
        if commandqueue[0]==3:
            responsequeue = commandqueue[2]
            frame = commandqueue[1]
            # This frame could have been read recently by a previous read request, so check again if it's necessary to read
            if time.time()-frame.timestamp > 8.0:
                sendFrame = addCheckSum(frame.pollFrame)+"\r"
                logger.debug('sendFrame = '+sendFrame)
                logger.debug('serial write')
                ser.write(sendFrame+'\r')   
                logger.debug('serial written')  
                line=""
                try:
                    ser.flushInput()
                    line=str(ser.read(frame.getLength())) 
                    logger.debug('serial read'+line)
                except:
                    logger.debug('Serial read error')
                if line:    
                    logger.debug('Got answer, parsing') 
                    result=commandqueue[1].parse(line)
                    try:
                        responsequeue.put(result)
                    except:
                        logger.debug('command response queue put 1 fail')               
                else: 
                    try:
                        logger.debug('Try to put False, answer was empty')
                        responsequeue.put(False)
                    except:
                        logger.debug('command response queue put 2 fail')               
                    logger.info('Empty, no answer')
            else: 
                responsequeue.put(True)
            
# Poll data and update the RRD database
def handlerThread():
        logger.debug('handlerTread started by signal handler')
        items=[]
        try:
            for data in pollData:
                items.append(getItem(data))
            s=':'.join(items)
            os.system("/usr/bin/rrdtool update "+db+" N:"+s)
            logger.setLevel(logging.INFO)
        except IOError as e:
            logger.setLevel(logging.DEBUG)
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

class Frame:
    def __init__(self, dd, frame):
        self.mutex=Lock()
        self.dataDef=dd 
        self.pollFrame=frame
        self.timestamp=0.0
        self.frameLength=0
        for i in self.dataDef:
            self.frameLength += i
        #include checksum byte
        self.frameLength+=1 
    
    def getLength(self):
        return self.frameLength
            
    def parse(self, s):
        logger.debug('Check checksum in parse '+s)
        if checkCheckSum(s):
            logger.info('Parse: checksum error on response message: ' + s)
            return False
        logger.debug('Checksum OK')
        if s==addCheckSum('E1'):
            logger.info('Parse: response message = E1, data does not exist')    
            return False
        if s==addCheckSum('E0'):
            logger.info('Parse: response message = E0, checksum fail')  
            return False                        
        index=0
        self.data=[]    
        if self.frameLength == len(s):
            logger.debug('Correct length')
            self.mutex.acquire()
            self.timestamp=time.time()
            for i in self.dataDef:
                index2=index+i
                self.data.append(s[index:index2])
                index=index2
            self.mutex.release()
            logger.debug('Return True from parser')
            return True
        else:
            logger.info("Parse: wrong length "+str(len(s))+', expected '+str(self.frameLength))
            return False
        
    def get(self, index):
        self.mutex.acquire()
        data=self.data[index]
        self.mutex.release()
        return data

# Read data/parameter value
def getItem(param): 
        logger.debug('getitem')
        dataparam=dataBase[param]
        if hasattr(dataparam, 'frame'):
            ok=True
            # If the frame containing this data hasn't been read recently do it now
            if time.time()-dataparam.frame.timestamp > 8.0:
                try:
                    responseQueue = Queue.Queue(3)
                    try:  # Send "read parameter value" message to pollThread
                        q.put((3,dataparam.frame,responseQueue))
                        try:  # and wait for a response                 
                            ok=responseQueue.get(True, 5)
                        except:
                            ok=False
                            logger.info('GetItem: Response timeout')
                    except:
                        ok=False
                        logger.info('Getitem: MessageQueue full')
                except:
                    logger.info('Getitem: Create responsequeue failed') 
                    ok=False
            if (ok):
                if dataparam.decimals == -1: # not a number, return as is
                    return dataparam.frame.get(dataparam.index)
                else:
                    try:
                        formatStr="{:0."+str(dataparam.decimals)+"f}"
                        return  formatStr.format( float(dataparam.frame.get(dataparam.index)) / pow(10, dataparam.decimals)  )
                    except:
                        raise IOError(0, "Getitem result is not a number")
            else:
                raise IOError(0, "GetItem failed")
        else: 
            raise IOError(0, "A command can't be read") 

# Write a parameter/command  
def setItem(param, s):
    dataparam=dataBase[param]
    if hasattr(dataparam, 'address'):
        try:
            value=float(s)
        except:
            return "not a number"
        if hasattr(dataparam, 'frame'):
            # Indicate that this frame has old data now
            dataparam.frame.timestamp = 0.0
        if hasattr(dataparam, 'decimals'):
            decimals = dataparam.decimals
        else:
            decimals = 0

        if value >= dataparam.min and value <= dataparam.max:
            s=("{:0>4.0f}".format(value * pow(10, decimals)))
            # Send "write parameter value" message to pollThread
            responseQueue = Queue.Queue() 
            q.put((2,dataparam.address + s, responseQueue))
            response = responseQueue.get()
            if response == addCheckSum('OK'):
                logger.info('Parameter %s = %s'%(param,s))
            return response
        else:
            return "Expected value "+str(dataparam.min)+".."+str(dataparam.max)
    else:
        return 'Not a setting value'

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
        
        logger.info('starting pelletMonitor')
        
        # Create SIGTERM signal handler
        signal.signal(signal.SIGTERM, sigterm_handler)

        # Create and start poll_thread
        POLLTHREAD = threading.Thread(name='poll_thread', target=pollThread)
        POLLTHREAD.setDaemon(True)
        POLLTHREAD.start()

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
    # message queue, used to send frame polling commands to pollThread
    global q
    q = Queue.Queue(300)

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

    # 'param' type is for setting values that can be read and written
    # 'data' type is for read-only measurement values
    # 'command' type is for write-only data
    param   = namedtuple('param',   'frame index decimals address min max') 
    data    = namedtuple('data',    'frame index decimals') 
    command = namedtuple('command', 'address min max')

    global version_string
    version_string = parser.get('conf', 'chipversion')

    if version_string == 'auto':
        # This frame had better be the same in all chip versions
        global FrameZ04
        FrameZ04  = Frame([5,5],'Z040000')
        global dataBase
        dataBase = {'version': data (FrameZ04,  1,    -1) }
        # PollThread not running yet so it's work is done here for version reading
        try:
            v = dataBase['version']
            sendFrame = addCheckSum(v.frame.pollFrame)+"\r"
            ser.write(sendFrame+'\r')   
            line=""
            try:
                ser.flushInput()
                line=str(ser.read(v.frame.getLength())) 
            except:
                logger.debug('Serial read error')
            if line:    
                v.frame.parse(line)
                version_string = v.frame.get(v.index).lstrip()
            else: 
                version_string=None
        except:
            logger.info('Chip version detection failed') 
            version_string = None        

    if version_string == None:
        version_string = '0.0'

    logger.info('Chip version: %s'%version_string)    

    global FrameZ00
    global FrameZ01
    global FrameZ02
    global FrameZ03
    global FrameZ05
    global FrameZ06
    global FrameZ07
    global FrameZ08

    # 'FrameXXX' defines the serial bus response frame format
    # [list of character count per value], 'string with the frame address'
    FrameZ00  = Frame([5,5,5,5,5,5,5,10,10,5,5,5,5,5,5,5,5,5],'Z000000')
    FrameZ01  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5], 'Z010000')
    FrameZ02  = Frame([10,10,10,10],'Z020000')
    FrameZ03  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z030000')
    FrameZ04  = Frame([5,5],'Z040000')
    FrameZ05  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z050000')
    FrameZ06  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z060000')
    FrameZ07  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z070000')    
    FrameZ08  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z080000')    

    # Dictionary of parameter names and their protocol mappings.
    # The protocol mapping is itself a dictionary with "start from" and "end at" version strings 
    # as key and a param, data or command named tuple as value. This way a parameter name can have
    # several protocol mappings identified by the version identifier. 

    dataBaseMap =  {
        
    #    parameter name             versions        type   frame   index decimals  
        'power':                { ('0000','zzzz') : data (FrameZ00,  0,     0) }, # Z00 is probably supported on all version
        'power_kW':             { ('0000','zzzz') : data (FrameZ00,  1,     1) },
        'boiler_temp':          { ('0000','zzzz') : data (FrameZ00,  2,     1) }, 
        'chute_temp':           { ('0000','zzzz') : data (FrameZ00,  3,     0) },
        'smoke_temp':           { ('0000','zzzz') : data (FrameZ00,  4,     0) },
        'oxygen':               { ('0000','zzzz') : data (FrameZ00,  5,     1) },
        'light':                { ('0000','zzzz') : data (FrameZ00,  6,     0) },
        'feeder_time':          { ('0000','zzzz') : data (FrameZ00,  7,     0) },
        'ignition_time':        { ('0000','zzzz') : data (FrameZ00,  8,     0) },
        'alarm':                { ('0000','zzzz') : data (FrameZ00,  9,     0) },
        'oxygen_desired':       { ('0000','zzzz') : data (FrameZ00, 11,     1) }, 
        'mode':                 { ('0000','zzzz') : data (FrameZ00, 16,     0) },
        'model':                { ('0000','zzzz') : data (FrameZ00, 17,     0) },
        'motor_time':           { ('0000','zzzz') : data (FrameZ02,  0,     0) },
        'el_time':              { ('0000','zzzz') : data (FrameZ02,  1,     0) },
        'motor_time_perm':      { ('0000','zzzz') : data (FrameZ02,  2,     0) },
        'el_time_perm':         { ('0000','zzzz') : data (FrameZ02,  3,     0) },
        'ignition_count':       { ('4.99','zzzz') : data (FrameZ03,  8,     0) },
        'boiler_return_temp':   { ('6.03','zzzz') : data (FrameZ06,  0,     0) },
        'hotwater_temp':        { ('6.03','zzzz') : data (FrameZ06,  1,     0) },
        'outside_temp':         { ('6.03','zzzz') : data (FrameZ06,  2,     0) },
        'indoor_temp':          { ('6.03','zzzz') : data (FrameZ06,  3,     0) },
        'flow':                 { ('6.03','zzzz') : data (FrameZ06,  4,     0) },
        'version':              { ('0000','zzzz') : data (FrameZ04,  1,    -1) }, # decimals = -1 means that this is a string, not a number

    #    parameter name             versions        type   frame    index  dec    addr   min    max
        'blower_low':           { ('4.99','zzzz') : param (FrameZ01,  0,    0,    'A00',   4,    50) },
        'blower_high':          { ('4.99','zzzz') : param (FrameZ01,  1,    0,    'A01',   5,   100) },
        'blower_mid':           { ('4.99','zzzz') : param (FrameZ03, 14,    0,    'A06',   5,    75) },
        'blower_cleaning':      { ('4.99','zzzz') : param (FrameZ01,  4,    0,    'A04',  25,   200) },
        'boiler_temp_set':      { ('0000','zzzz') : param (FrameZ00, 10,    0,    'B01',  40,    85) },
        'boiler_temp_min':      { ('4.99','zzzz') : param (FrameZ01,  9,    0,    'B03',  10,    70) },
        'feeder_low':           { ('4.99','zzzz') : param (FrameZ01, 10,    2,    'B04',   0.5,  25) },
        'feeder_high':          { ('4.99','zzzz') : param (FrameZ01, 11,    1,    'B05',   1,   100) },
        'feed_per_minute':      { ('4.99','zzzz') : param (FrameZ01, 12,    0,    'B06',   1,     3) },

        'boiler_temp_diff_up':  { ('4.99','zzzz') : param (FrameZ01, 17,    0,    'C03',   0,    20) },
        'boiler_temp_diff_down':{ ('4.99','zzzz') : param (FrameZ03, 13,    0,    'C04',   0,    15) },

        'light_required':       { ('4.99','zzzz') : param (FrameZ01, 22,    0,    'D03',   0,   100) },

        'oxygen_regulation':    { ('4.99','zzzz') : param (FrameZ01, 23,    0,    'E00',   0,     2) },
        'oxygen_low':           { ('4.99','zzzz') : param (FrameZ01, 24,    1,    'E01',  10,    19) },
        'oxygen_high':          { ('4.99','zzzz') : param (FrameZ01, 25,    1,    'E02',   2,    12) },
        'oxygen_mid':           { ('6.50','zzzz') : param (FrameZ08, 7,     1,    'E06',   0,    21) },
        'oxygen_gain':          { ('4.99','zzzz') : param (FrameZ01, 26,    2,    'E03',   0,    99.99) },

        'feeder_capacity_min':  { ('4.99','zzzz') : param (FrameZ01, 27,    0,    'F00', 400,  2000) },
        'feeder_capacity':      { ('0000','zzzz') : param (FrameZ00, 12,    0,    'F01', 400,  8000) },
        'feeder_capacity_max':  { ('4.99','zzzz') : param (FrameZ01, 29,    0,    'F02', 400,  8000) },

    #    parameter name             versions        type   frame    index  dec    addr   min    max
        'chimney_draught':      { ('0000','zzzz') : param (FrameZ00, 13,    0,    'G00',   0,    10) },
        'chute_temp_max':       { ('4.99','zzzz') : param (FrameZ01, 31,    0,    'G01',  50,    90) },
        'regulator_P':          { ('4.99','zzzz') : param (FrameZ01, 32,    1,    'G02',   1,    20) },
        'regulator_I':          { ('4.99','zzzz') : param (FrameZ01, 33,    2,    'G03',   0,     5) },
        'regulator_D':          { ('4.99','zzzz') : param (FrameZ01, 34,    1,    'G04',   1,    50) },
        'blower_corr_low':      { ('4.99','zzzz') : param (FrameZ01, 39,    0,    'G05',  50,   150) },
        'blower_corr_high':     { ('4.99','zzzz') : param (FrameZ01, 40,    0,    'G06',  50,   150) },
        'cleaning_interval':    { ('4.99','zzzz') : param (FrameZ01, 41,    0,    'G07',   1,   120) },
        'cleaning_time':        { ('4.99','zzzz') : param (FrameZ01, 42,    0,    'G08',   0,    60) },
        'language':             { ('0000','zzzz') : param (FrameZ04, 0,     0,    'G09',   0,     3) },

        'autocalculation':      { ('4.99','zzzz') : param (FrameZ03, 10,    0,    'H04',   0,     1) },
        'time_minutes':         { ('4.99','zzzz') : param (FrameZ01, 44,    0,    'H07',   0,  1439) },

        'oxygen_corr_10':       { ('4.99','zzzz') : param (FrameZ03, 1,     0,    'I00',   0,   100) },
        'oxygen_corr_50':       { ('4.99','zzzz') : param (FrameZ03, 2,     0,    'I01',   0,   100) },
        'oxygen_corr_100':      { ('4.99','zzzz') : param (FrameZ03, 3,     0,    'I02',   0,   100) },
        'oxygen_corr_interval': { ('4.99','zzzz') : param (FrameZ03, 4,     0,    'I03',   1,    60) },
        'oxygen_regulation_P':  { ('4.99','zzzz') : param (FrameZ03, 5,     2,    'I04',   0,     5) },
        'oxygen_regulation_D':  { ('4.99','zzzz') : param (FrameZ03, 6,     0,    'I05',   0,   100) },
        'blower_off_time':      { ('4.99','zzzz') : param (FrameZ03, 9,     0,    'I07',   0,    30) },

        'timer_heating_period': { ('6.03','zzzz') : param (FrameZ05, 9, 	0,    'K00',   0,  1440) },
        'timer_hotwater_period':{ ('6.03','zzzz') : param (FrameZ05, 10, 	0,    'K01',   0,  1440) },
        'timer_heating_start_1':{ ('6.03','zzzz') : param (FrameZ05, 11, 	0,    'K02',   0,  1439) },
        'timer_heating_start_2':{ ('6.03','zzzz') : param (FrameZ05, 12, 	0,    'K03',   0,  1439) },
        'timer_heating_start_3':{ ('6.03','zzzz') : param (FrameZ05, 13, 	0,    'K04',   0,  1439) },
        'timer_heating_start_4':{ ('6.03','zzzz') : param (FrameZ05, 14, 	0,    'K05',   0,  1439) },
        'timer_hotwater_start_1':{('6.03','zzzz') : param (FrameZ05, 15, 	0,    'K06',   0,  1439) },
        'timer_hotwater_start_2':{('6.03','zzzz') : param (FrameZ05, 16, 	0,    'K07',   0,  1439) },
        'timer_hotwater_start_3':{('6.03','zzzz') : param (FrameZ05, 17, 	0,    'K08',   0,  1439) },

        'comp_clean_interval':  { ('6.03','zzzz') : param (FrameZ05, 18,    0,    'L00',   0,    21) },
        'comp_clean_time':      { ('6.03','zzzz') : param (FrameZ05, 19,    0,    'L01',   0,    10) },
        'comp_clean_blower':    { ('6.03','zzzz') : param (FrameZ05, 20,    0,    'L02',   0,   100) },
        'comp_clean_wait':      { ('6.12','zzzz') : param (FrameZ05, 29,    0,    'L03',   0,   300) },

        'blower_corr_mid':      { ('4.99','zzzz') : param (FrameZ05, 22,    0,    'M00',  50,   150) },

    #    parameter name             versions        type   frame    index  dec    addr   min    max
        'min_power':            { ('4.99','zzzz') : param (FrameZ01, 37,    0,    'H02',  10,   100) },
        'max_power':            { ('4.99','zzzz') : param (FrameZ01, 38,    0,    'H03',  10,   100) },

        'burner_off':           { ('4.99','zzzz') : command (                     'V00',   0,     0) },
        'burner_on':            { ('4.99','zzzz') : command (                     'V01',   0,     0) },
        'reset_alarm':          { ('4.99','zzzz') : command (                     'V02',   0,     0) },
    }   

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

    # Build a dictionary of parameters supported on version_string
    dataBase={}
    for param_name in dataBaseMap:
        mappings = dataBaseMap[param_name]
        for supported_versions in mappings: 
            if version_string >= supported_versions[0] and version_string < supported_versions[1]:
                dataBase[param_name] = mappings[supported_versions]


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
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)



