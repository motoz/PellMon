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

from threading import Lock
from logging import getLogger 
import time
from collections import namedtuple
import Queue
import threading
import serial

from datamap import dataBaseMap

logger = getLogger('pellMon')
dataBase = {}

# 'param' type is for setting values that can be read and written
# 'data' type is for read-only measurement values
# 'command' type is for write-only data
param   = namedtuple('param',   'frame index decimals address min max') 
data    = namedtuple('data',    'frame index decimals') 
command = namedtuple('command', 'address min max')

def initProtocol(dev, version_string):   
    """Initialize the protocol and database according to given version"""    
         
    # message queue, used to send frame polling commands to pollThread
    global q
    global ser
    global dataBase

    # Open serial port
    ser = serial.Serial()
    ser.port     = dev
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
        
    q = Queue.Queue(300)
    dataBase = createDataBase('0000')
    
    # Create and start poll_thread
    POLLTHREAD = threading.Thread(name='poll_thread', target=pollThread)
    POLLTHREAD.setDaemon(True)
    POLLTHREAD.start()

    if version_string == 'auto':
        try:
            version_string = getItem('version').lstrip()
            logger.info('chip version: %s'%version_string)
        except:
            version_string = '0.0'
            logger.info('version detection failed')
    dataBase = createDataBase(version_string)
        
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

def getDataBase():
    return dataBase  
            
def getItem(param): 
    """Read data/parameter value"""
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

def setItem(param, s):
    """Write a parameter/command"""
    dataparam=dataBase[param]
    if hasattr(dataparam, 'address'):
        try:
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
        except Exception, e:
            return e
    else:
        return 'Not a setting value'        
        
def createDataBase(version_string):
    """return a dictionary of parameters supported on version_string"""
    db={}
    for param_name in dataBaseMap:
        mappings = dataBaseMap[param_name]
        for supported_versions in mappings: 
            if version_string >= supported_versions[0] and version_string < supported_versions[1]:
                db[param_name] = mappings[supported_versions]
    return db   

def pollThread():
    """Waits on global queue 'q' for frame read / parameter write commands, responds in an 
    other queue received with the command"""
    while True:  
        commandqueue = q.get() 

        # Write parameter/command       
        if commandqueue[0]==2:
            s=addCheckSum(commandqueue[1])
            logger.debug('serial write'+s)
            ser.flushInput()
            ser.write(s+'\r')   
            logger.debug('serial written'+s)        
            line=""
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

                line=""
                try:
                    ser.flushInput()
                    logger.debug('serial write')
                    ser.write(sendFrame+'\r')   
                    logger.debug('serial written')  
                    line=str(ser.read(frame.getLength())) 
                    logger.debug('serial read'+line)
                except:
                    logger.debug('Serial read error')
                result = False
                if line:    
                    logger.debug('Got answer, parsing') 
                    result=commandqueue[1].parse(line)
                    if result:
                        try:
                            responsequeue.put(result)
                        except:
                            logger.debug('command response queue put 1 fail')    
                else:
                    logger.info('Timeout')
                if not result:           
                    logger.info('Retrying')
                    try:
                        ser.flushInput()
                        logger.debug('serial write')
                        ser.write(sendFrame+'\r')
                        logger.debug('serial written')
                        line=str(ser.read(frame.getLength()))
                        logger.debug('answer: '+line)
                    except:
                        logger.debug('Serial read error')
                    if line:
                        logger.info('Got answer, parsing')
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
                        logger.info('Timeout again, give up and return fail')

            else: 
                responsequeue.put(True)         
              
