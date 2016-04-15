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
from exceptions import *

class Proxy:
    root = ('settings', 'operating_data', 'advanced_data', 'consumption_data', 'event_log','sw_versions','info')
    settings = ('boiler', 'hot_water', 'regulation', 'weather', 'oxygen', 'cleaning', 'hopper', 'fan', 'auger', 'ignition', 'pump', 
        'sun', 'vacuum', 'misc', 'alarm', 'manual')
    consumption_data = ('total_hours', 'total_days', 'total_months', 'total_years', 'dhw_hours', 'dhw_days', 'dhw_months', 'dhw_years', 'counter')

    def __init__(self, password, port=1920, addr=None, version='V3', serial=None):
        self.password = password
        self.addr = (addr, port)
        self.lock = threading.Lock()
        self.serial = serial

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if addr == '<broadcast>':
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.4)
        self.s = s
        if version == '3':
            self.request = V3_request_frame()
            self.response = V3_response_frame(self.request)
        elif version == '2':
            self.request = V2_request_frame()
            self.response = V2_response_frame(self.request)
        elif version == '1':
            self.request = V1_request_frame()
            self.response = V1_response_frame(self. request)
        self.request.pincode = self.password

        if not self.find_controller():
            logger.info('Controller not found')
            raise Exception
        self.get_rsakey()
        self.set_xteakey()
        self.t = threading.Thread(target=lambda:self.xtea_refresh_thread())
        self.t.setDaemon(True)
        self.t.start()
        self.dir()

    def get_rsakey(self):
        with self.lock:
            request = self.request
            request.payload = 'misc.rsa_key'
            request.function = 1
            request.sequencenumber += 1
            for retry in range(3):
                try:
                    self.s.sendto(request.encode() , self.addr)
                    while True:
                        try:
                            data, server = self.s.recvfrom(4096)
                            self.response.decode(data)
                        except seqnum_error as e:
                            print (e)
                            request.public_key = None
                            time.sleep(1)
                        else:
                            break
                    key = self.response.payload.split('rsa_key=')[1]
                    key = base64.b64decode(key)
                    request.public_key = RSA.importKey(key)
                except socket.timeout:
                    print 'timout'
                    time.sleep(1)
                else:
                    return True 
        return False
    
    def set_xteakey(self):
        #print 'xxsend'
        xtea_key = ''.join([chr(SystemRandom().randrange(128)) for x in range(16)])
        r = self.set('settings/misc/xtea_key', xtea_key)
        if not r== ('ok',):
            print 'xtea set failed'
        self.request.xtea_key = xtea.new(xtea_key, mode=xtea.MODE_ECB, IV='\00'*8, rounds=64, endian='!')

    def find_controller(self):
        with self.lock:
            request = self.request
            request.function = 0
            request.payload = 'NBE_DISCOVERY'
            request.sequencenumber = randrange(0,100)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            for retry in range(5):
                try:
                    request.sequencenumber = randrange(0,100)
                    self.s.sendto(request.encode(), self.addr)
                    while True:
                        try:
                            data, server = self.s.recvfrom(4096)
                            print data, server
                            self.response.decode(data)
                            self.addr = server
                            res = self.response.parse_payload()
                            if self.serial:
                                if 'Serial' in res and res['Serial'] == self.serial:
                                    self.ip = res['IP']
                                    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                                    break
                            else:
                                self.ip = res['IP']
                                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                                break
                        except seqnum_error:
                            pass
                except socket.timeout:
                    print 'timeout'
                    time.sleep(1)
                else:
                    return True
            return False

    def dir(self):
        dirlist = []
        for s in self.settings:
            dl = self.make_request(3, s+'.*').payload.encode('ascii').split(';')
            for d in dl:
                d_name, d = d.split('=')
                d_min, d_max, d_default, d_decimals = d.split(',')
                dirlist.append({'path':s+'.'+d_name, 'name':d_name, 'function':1, 'grouppath':s+'.*', 'group':s, 'min':d_min, 'max':d_max, 'decimals':d_decimals, 'type':'R/W', 'value':'-'})
        dl = self.make_request(5, '*').payload.encode('ascii').split(';')
        for d in dl:
            d_name, d_value = d.split('=')
            dirlist.append({'path':d_name, 'name':d_name, 'function':5, 'grouppath':'*', 'group':'advanced_data', 'type':'R', 'value':d_value})
        dl = self.make_request(4, '*').payload.encode('ascii').split(';')
        for d in dl:
            d_name, d_value = d.split('=')
            dirlist.append({'path':d_name, 'name':d_name, 'function':4, 'grouppath':'*', 'group':'operating_data', 'type':'R', 'value':d_value})
        #dl = self.make_request(6, 'counter').payload
        #d_name, d_value = dl.split('=')
        d_name = 'counter'
        dirlist.append({'path':d_name, 'name':d_name, 'function':6, 'group':'consumption_data', 'type':'R', 'value':d_value})
        return dirlist

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
                #self.request.xtea_key = xtea.new(' '*16, mode=xtea.MODE_ECB, IV='\00'*8, rounds=64, endian='!')
                self.s.settimeout(5)
                response = self.make_request(2, '.'.join(d[1:3]) + '=' + value, encrypt=True)
                #print 'set response', response.status
                self.s.settimeout(0.4)
                if response.status == 0:
                    return ('ok',)
                else:
                    return (response.payload,)
        else:
            return self.get(path)

    @classmethod
    def discover(cls, password, port, version='V3', serial=None):
        return cls(password, port, addr='<broadcast>', version=version, serial=serial)

    def make_request(self, function, payload, encrypt=False, key=None):
        for retry in range(3):
            try:
                self.request.sequencenumber += 1
                if self.request.sequencenumber > 99:
                    self.request.sequencenumber = 0
                self.request.payload = payload
                self.request.function = function
                self.request.encrypted = encrypt
                #print 'encrypt flag', self.request.encrypted
                self.request.pincode = self.password
                self.s.sendto(self.request.encode(), self.addr)
                #print(' '.join([hex(ord(ch)) for ch in c.framedata]))
                #print 'sent:', self.request.encode()
                while True:
                    try:
                        while True:
                            try:
                                data, server = self.s.recvfrom(4096)
                            except socket.error as e:
                                if e.errno != errno.EINTR:
                                    raise
                            else:
                                break
                        self.response.decode(data)
                        #print 'received:', data, len(data)
                        return self.response
                    except seqnum_error as e:
                        print 'seqnum error, reread', payload, str(function)
                        pass #just read again on seqnum error
                    else:
                        break
            except socket.timeout:
                print 'timeout, retry', retry
                if retry == 2:
                    raise socket.timeout

    def xtea_refresh_thread(self):
        while True:
            time.sleep(5)
            try:
                self.set_xteakey()
            except Exception as e:
                del self.request.xtea_key
                #print 'error setting xtea, try with rsa', str(e), str(time.ctime())
                try:
                    self.set_xteakey()
                except Exception as e:
                    #print 'failed, try again in 5 s'
                    pass


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



