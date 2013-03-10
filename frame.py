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

logger = getLogger('pellMon')

# 'param' type is for setting values that can be read and written
# 'data' type is for read-only measurement values
# 'command' type is for write-only data
param   = namedtuple('param',   'frame index decimals address min max') 
data    = namedtuple('data',    'frame index decimals') 
command = namedtuple('command', 'address min max')


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
