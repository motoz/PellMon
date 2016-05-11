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

import time
from protocolexceptions import *
from random import SystemRandom

START = b'\x02'
END = b'\x04'
STATUS_CODES = (0,1,2,3)
FUNCTION_CODES = (0,1,2,3,4,5,6,7,8,9,10,11)

class Request_frame(object):
    def __init__(self, version = 'V1'):
        self.REQUEST_HEADER_SIZE = 52
        self.appid = ''.join([chr(SystemRandom().randrange(128)) for x in range(12)])
        self.controllerid = 'id'
        self.encrypted = False
        self.sequencenumber = 0
        self.pincode = '0123456789'
        self.payload = ''
        self.payloadsize = len(self.payload)
        self.function = 0

    def encode(self):
        self.framedata = ('%12s'%self.appid[:12]).encode('ascii')
        self.framedata += ('%6s'%self.controllerid[:6]).encode('ascii')

        if self.encrypted:
            if hasattr(self, 'xtea_key'):
                self.framedata += ('%1s'%'-').encode('ascii')
            else:
                self.framedata += ('%1s'%'*').encode('ascii')
        else:
            self.framedata += ('%1s'%' ').encode('ascii')

        h = START;
        if self.function not in FUNCTION_CODES:
            raise IOError
        h += ('%02u'%self.function).encode('ascii')
        h += ('%02d'%self.sequencenumber).encode('ascii')

        if self.encrypted:
            h += ('%10s'%self.pincode[:10]).encode('ascii')
        else:
            h += ('-'*10).encode('ascii')
        h += ('%10s'%int(time.time())).encode('ascii')
        h += ('%4s'%'extr').encode('ascii')
        h += ('%03u'%len(self.payload)).encode('ascii')
        if len(self.payload) > 495:
            raise IOError
        try:
            h += self.payload.encode('ascii')
        except UnicodeError:
            h += self.payload
        h += END;
        pad = b'0'*(64-len(h))
        h+=pad
        if self.encrypted: 
            if hasattr(self, 'xtea_key'):
                h = self.xtea_key.encrypt(h)
            else:
                h = self.public_key.encrypt(h, None)[0]
        self.framedata += h
        return self.framedata

    def decode(self, record):
        i = 0
        self.appid = record[i:12]
        i+=12
        self.controllerid = record[i:6]
        i+=6
        self.encryption = record[i:1]
        i+=1
        if not record[i] == START[0]:
            raise IOError
        if len(record) < 17:
            raise IOError
        i += 1
        self.function = int(record[i:i+2])
        i += 2
        self.sequencenumber = int(record[i:i+2])
        i += 2
        self.pincode = record[i:i+10].decode('ascii')
        i += 10
        self.timestamp = int(record[i:i+10].decode('ascii'))
        i += 10
        self.extra = record[i:i+4].decode('ascii')
        i += 4
        self.payloadsize = int(record[i:i+3])
        i += 3
        if len(record) < self.payloadsize + self.REQUEST_HEADER_SIZE:
            raise IOError
        self.payload = record[i:i+self.payloadsize]
        i += self.payloadsize
        if not record[i] == END[0]:
            raise IOError

class Response_frame(object):
    def __init__(self, request):
        self.RESPONSE_HEADER_SIZE = 28
        self.request = request

    def encode(self):
        self.framedata = ('%12s'%self.request.appid).encode('ascii')
        self.framedata += ('%6s'%self.request.controllerid).encode('ascii')
        self.framedata += START;
        if int(self.function) > 13:
            raise protocol_error
        self.framedata += ('%02u'%self.function).encode('ascii')
        if self.status not in STATUS_CODES:
            raise protocol_error
        self.framedata += ('%2d'%self.request.sequencenumber).encode('ascii')
        self.framedata += ('%1s'%self.status).encode('ascii')
        if len(self.payload) > 1007:
            raise protocol_error
        self.framedata += ('%03u'%len(self.payload)).encode('ascii')
        self.framedata += self.payload.encode('ascii')
        self.framedata += END;
        return self.framedata

    def decode(self, record):
        self.framedata = record
        i = 0
        self.appid = record[i:i+12]
        i+=12
        self.controllerid = record[i:i+6]
        i+=6
        if not record[i] == START[0]:
            raise protocol_error('start missing')
        if len(record) < self.RESPONSE_HEADER_SIZE:
            raise protocol_error('too long length')
        i += 1
        try:
            self.function = int(record[i:i+2])
        except:
            self.function = None
        i += 2
        try:
            self.sequencenumber = int(record[i:i+2])
        except:
            self.sequencenumber = '-'
        i += 2
        self.status = int(record[i:i+1])
        i += 1
        self.size = int(record[i:i+3])
        i += 3
        if not len(record) == self.size + self.RESPONSE_HEADER_SIZE:
            raise protocol_error('wrong length')
        self.payload = (record[i:i+self.size]).decode('ascii')
        i += self.size
        if not record[i] == END[0]:
            raise protocol_error('end missing')
        if self.sequencenumber != self.request.sequencenumber:
            raise seqnum_error('---seqnum, res:%s req:%s'%(str(self.sequencenumber), str(self.request.sequencenumber)))

    def parse_payload(self):
        frame = self.payload
        d = {}
        for item in frame.split(';'):
            name, value = item.split('=')
            d[name] = value
        return d

