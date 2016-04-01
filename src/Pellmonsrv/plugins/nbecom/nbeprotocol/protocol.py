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

import socket
from random import randrange, SystemRandom
import time
from Crypto.PublicKey import RSA
import base64
import threading
import errno
from v3frames import V3_request_frame, V3_response_frame
from v2frames import V2_request_frame, V2_response_frame
from v1frames import V1_request_frame, V1_response_frame
import xtea

class Proxy:
    root = ('settings', 'operating_data', 'advanced_data', 'consumption_data', 'event_log','sw_versions','info')
    settings = ('boiler', 'hot_water', 'regulation', 'weather', 'oxygen', 'cleaning', 'hopper', 'fan', 'auger', 'ignition', 'pump', 
        'sun', 'vacuum', 'misc', 'alarm', 'manual')
    consumption_data = ('total_hours', 'total_days', 'total_months', 'total_years', 'dhw_hours', 'dhw_days', 'dhw_months', 'dhw_years', 'counter')

    def __init__(self, password, port=1900, addr=None, version='V3'):
        self.password = password
        self.addr = (addr, port)
        self.lock = threading.Lock()

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if addr == '<broadcast>':
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2)
        self.s = s
        if version == '3':
            request = V3_request_frame()
            self.response = V3_response_frame(request)
        elif version == '2':
            request = V2_request_frame()
            self.response = V2_response_frame(request)
        elif version == '1':
            request = V1_request_frame()
            self.response = V1_response_frame(request)

        request.function = 0
        request.payload = 'NBE_DISCOVERY'
        request.sequencenumber = randrange(0,100)
        with self.lock:
            self.s.sendto(request.encode() , (addr, port))
            data, server = self.s.recvfrom(4096)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
            self.addr = server
            self.response.decode(data)
            res = self.response.parse_payload()
        if 'Serial' in res:
            self.serial = res['Serial']
        if 'IP' in res:
            self.ip = res['IP']

        with self.lock:
            request.payload = 'misc.rsa_key'
            request.function = 1
            request.sequencenumber += 1
            self.s.sendto(request.encode() , self.addr)
            data, server = self.s.recvfrom(4096)
            self.response.decode(data)
            try:
                key = self.response.payload.split('rsa_key=')[1]
                key = base64.b64decode(key)
                request.public_key = RSA.importKey(key)
            except Exception as e:
                print (e)
                request.public_key = None
            request.pincode = self.password
            self.request = request
        xtea_key = ''.join([chr(SystemRandom().randrange(128)) for x in range(16)])
        print xtea_key
        self.set('settings/misc/xtea_key', xtea_key)
        self.request.xtea_key = xtea.new(xtea_key, mode=xtea.MODE_ECB, IV='\00'*8, rounds=64, endian='!')

    def get(self, d=None):
        d = d.rstrip('/').split('/')
        if d[0] is None or d[0] is '*':
            return [p + '/' for p in self.root]
        elif d[0] == 'settings':
            if len(d) == 1:
                return ['settings/%s/'%s for s in self.settings]
            elif d[1] in self.settings:
                if len(d) == 2:
                    with self.lock:
                        response = self.make_request(1, d[1] + '.*')
                        return ['settings/%s/%s'%(d[1], s) for s in response.payload.split(';')]
                else:
                    with self.lock:
                        response = self.make_request(1, d[1] + '.' + d[2])
                        try:
                            return (response.payload.split('=', 1)[1],)
                        except IndexError:
                            return (response.payload,)
            else:
                return []
        elif d[0] in ('operating_data', 'advanced_data'):
            if d[0] == 'operating_data':
                f = 4
            else:
                f = 5
            if len(d) == 1:
                with self.lock:
                    response = self.make_request(f, '*')
                    return [d[0] + '/' + s for s in response.payload.split(';')]
            elif len(d) == 2:
                with self.lock:
                    response = self.make_request(f, d[1])
                    try:
                        return (response.payload.split('=')[1],)
                    except IndexError:
                        return (response.payload,)
        elif d[0] == 'consumption_data':
            if len(d) == 1:
                return [d[0] + '/' + s for s in self.consumption_data]
            elif d[1] in self.consumption_data:
                with self.lock:
                    response = self.make_request(6, d[1])
                    return [d[0] + '/' + s for s in response.payload.split(';')]
            else:
                return []
        elif d[0] == 'sw_versions':
            if len(d) == 1:
                with self.lock:
                    response = self.make_request(10, '')
                    return [s for s in response.payload.split(';')]
            else:
                return []
        elif d[0] == 'info':
            if len(d) == 1:
                with self.lock:
                    response = self.make_request(9, '')
                    return [s for s in response.payload.split(';')]
            else:
                return []
        elif d[0] == 'event_log':
            if len(d) == 1:
                now = time.strftime('%y%m%d:%H%M%S;',time.localtime())
                with self.lock:
                    response = self.make_request(8, now)
                    return response.payload.split(';')
            else:
                with self.lock:
                    response = self.make_request(8, d[1])
                    return response.payload.split(';')

    def set(self, path=None, value=None):
        d = path.rstrip('/').split('/')
        if d[0] is None or d[0] is '*':
            return ('settings',)
        elif len(d) == 3 and d[1] in self.settings and value is not None :
            with self.lock:
                self.s.settimeout(5)
                response = self.make_request(2, '.'.join(d[1:3]) + '=' + value, encrypt=True)
                self.s.settimeout(2)
                if response.status == 0:
                    return ('ok',)
                else:
                    return (response.payload,)
        else:
            return self.get(path)

    @classmethod
    def discover(cls, password, port, version='V1'):
        return cls(password, port, addr='<broadcast>', version=version)

    def make_request(self, function, payload, encrypt=False, key=None):
        #print(' '.join([hex(ord(ch)) for ch in c.framedata]))
        self.request.sequencenumber += 1
        if self.request.sequencenumber > 99:
            self.request.sequencenumber = 0
        self.request.payload = payload
        self.request.function = function
        self.request.encrypted = encrypt
        self.request.pincode = self.password
        self.s.sendto(self.request.encode(), self.addr)
        while True:
            try:
                data, server = self.s.recvfrom(4096)
            except socket.error as e:
                print str(e)
                if e.errno != errno.EINTR:
                    raise
            else:
                break
        self.response.decode(data)
        return self.response

class Controller:
    def __init__(self, host, password, port=1900, seqnums=True):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind((host, port))
        self.password = password
        self.request = V3_request_frame()
        self.response = V3_response_frame(self.request)

        if seqnums:
            self.seqnums = 0
        else:
            self.seqnums = None

    def run(self):
        while True:
            d = self.s.recvfrom(1024)
            data = d[0]
            addr = d[1]
            self.request.decode(data)
            print ('< ' + self.request.payload.decode('ascii'))
            # discovery response
            if self.request.function == 0:
                self.response.function = self.request.function
                self.response.payload = 'Serial=1234;IP=%s'%addr[0]
                self.response.status = 0
                frame = self.response.encode()
                self.s.sendto(frame , addr)
                print ('  > ' + frame.decode('ascii'))
            else:
                # check password
                if True: #self.requset.pincode == self.password:
                    if self.request.function == 1:
                        self.response.function = self.request.function
                        if self.request.payload == 'boiler.temp':
                            self.response.payload = 'boiler.temp=90'
                            self.response.status = 0
                        elif self.request.payload == 'misc.rsa_key':
                            self.response.payload = 'casyugdyasguyagusduaysgdaysudyasgdyuasdgua'
                            self.response.status = 0
                        frame = self.response.encode()
                        self.s.sendto(frame , addr)
                    else:
                        self.response.function = self.request.function
                        self.response.payload = 'illegal function'
                        self.response.status = 1
                        frame = self.response.encode()
                        self.s.sendto(frame , addr)
                    print ('  > ' + frame.decode('ascii'))
                else:
                    self.response.function = self.request.function
                    self.response.payload = 'wrong password'
                    self.response.status = 1
                    frame = self.response.encode()
                    self.s.sendto(frame , addr)
                    print ('  > ' + frame.decode('ascii'))



