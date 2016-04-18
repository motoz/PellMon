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
    settings = ('boiler', 'hot_water', 'regulation', 'weather', 'oxygen', 'cleaning', 'hopper', 'fan', 'auger', 'ignition', 'pump', 
        'sun', 'vacuum', 'misc', 'alarm', 'manual')
#    consumption_data = ('total_hours', 'total_days', 'total_months', 'total_years', 'dhw_hours', 'dhw_days', 'dhw_months', 'dhw_years', 'counter')

    def __init__(self, password, port=1920, addr=None, version='V3', serial=None):
        self.password = password
        self.discover_addr = (addr, port)
        self.lock = threading.Lock()
        self.serial = serial
        self.controller_online = False
        

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if addr == '<broadcast>':
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.5)
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
        self.request.sequencenumber = randrange(0,100)

        self.t = threading.Thread(target=lambda:self.find_controller())
        self.t.setDaemon(True)
        self.t.start()

        self.t = threading.Thread(target=lambda:self.xtea_refresh_thread())
        self.t.setDaemon(True)
        self.t.start()


    def get_rsakey(self):
        if not self.controller_online:
            return False
        for retry in range(3):
            with self.lock:
                request = self.request
                request.payload = 'misc.rsa_key'
                request.function = 1
                request.sequencenumber += 1
                request.public_key = None
                try:
                    self.s.sendto(request.encode() , self.addr)
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
                            break
                        except seqnum_error as e:
                            print 'seqnum error get_rsakey', str(e), time.time()
                            pass
                    if self.response.status == 0:
                        key = self.response.payload.split('rsa_key=')[1]
                        key = base64.b64decode(key)
                        request.public_key = RSA.importKey(key)
                        return True 
                except Exception as e:
                    print 'other except, get_rsakey', str(e), time.time()
                    pass # retry 3 times
            time.sleep(1)
        return False
    
    def set_xteakey(self):
        xtea_key = ''.join([chr(SystemRandom().randrange(128)) for x in range(16)])
        r = self.set('misc.xtea_key', xtea_key)
        if r== 'ok':
            self.request.xtea_key = xtea.new(xtea_key, mode=xtea.MODE_ECB, IV='\00'*8, rounds=64, endian='!')
        else:
            try:
                print 'xtea_set fail, del key', time.time()
                del self.request.xtea_key
            except AttributeError:
                pass

    def set(self, path, value):
        if not self.controller_online:
            raise protocol_offline
        for retry in range(5):
            try:
                with self.lock:
                    if not hasattr(self.request, 'xtea_key'):
                        use_rsa = True
                    else:
                        use_rsa = False
                    if use_rsa:
                        self.s.settimeout(5)
                        print 'use rsa for xtea set', time.time()
                    response = self.make_request(2, path+'='+value, encrypt=True)
                    if use_rsa:
                        self.s.settimeout(0.5)
                    if response.status == 0:
                        return 'ok'
            except protocol_error:
                print 'set retry', retry
        print 'no more set retry'
        raise protocol_error

    def get(self, function, path, group=False):
        if not self.controller_online:
            raise protocol_offline
        for retry in range(5):
            try:
                with self.lock:
                    response = self.make_request(function, path)
                    if response.status == 0:
                        if not group:
                            return response.payload.encode('ascii').split('=', 1)[1]
                        else:
                            return response.payload.encode('ascii').split(';')
            except: #protocol_error:
                print 'get retry', retry, time.time()
        print 'no more get retry'
        raise protocol_error

    def find_controller(self):
        while True:
            try:
                controller_online = False
                for retry in range(3):
                    with self.lock:
                        request = self.request
                        request.function = 0
                        request.payload = 'NBE_DISCOVERY'
                        request.sequencenumber += 1
                        if request.sequencenumber >= 99:
                           request.sequencenumber = 0
                        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        try:
                            request.sequencenumber = randrange(0,100)
                            self.s.sendto(request.encode(), self.discover_addr)
                            while True:
                                try:
                                    data, server = self.s.recvfrom(4096)
                                    self.response.decode(data)
                                    self.addr = server
                                    res = self.response.parse_payload()
                                    if self.serial:
                                        if 'Serial' in res and res['Serial'] == self.serial:
                                            self.ip = res['IP']
                                            controller_online = True
                                            break
                                    else:
                                        self.ip = res['IP']
                                        controller_online = True
                                        break
                                except seqnum_error:
                                    pass
                        except Exception as e:
                            time.sleep(1)
                        else:
                            break
                        finally:
                            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)

                if controller_online and not self.controller_online:
                    self.controller_online = controller_online
                    self.get_rsakey()
                    self.set_xteakey()

                if not hasattr(self.request, 'xtea_key'):
                    self.get_rsakey()
                    self.set_xteakey()

                self.controller_online = controller_online

                if self.controller_online:
                    time.sleep(5)
                else:
                    time.sleep(1)
            except Exception as e:
                pass #don't ever die in this thread

    def dir(self):
        dirlist = []
        for s in self.settings:
            dl = self.get(3, s+'.*', group=True)
            for d in dl:
                d_name, d = d.split('=')
                d_min, d_max, d_default, d_decimals = d.split(',')
                dirlist.append({'path':s+'.'+d_name, 'name':d_name, 'function':1, 'grouppath':s+'.*', 'group':s, 'min':d_min, 'max':d_max, 'decimals':d_decimals, 'type':'R/W', 'value':'-'})

        dl = self.get(5, s+'.*', group=True)
        for d in dl:
            d_name, d_value = d.split('=')
            dirlist.append({'path':d_name, 'name':d_name, 'function':5, 'grouppath':'*', 'group':'advanced_data', 'type':'R', 'value':d_value})

        dl = self.get(4, s+'.*', group=True)
        for d in dl:
            d_name, d_value = d.split('=')
            dirlist.append({'path':d_name, 'name':d_name, 'function':4, 'grouppath':'*', 'group':'operating_data', 'type':'R', 'value':d_value})

        d_name = 'counter'
        dirlist.append({'path':d_name, 'name':d_name, 'function':6, 'group':'consumption_data', 'type':'R', 'value':d_value})
        return dirlist

    @classmethod
    def discover(cls, password, port, version='V3', serial=None):
        return cls(password, port, addr='<broadcast>', version=version, serial=serial)

    def make_request(self, function, payload, encrypt=False):
        try:
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
                    while True:
                        try:
                            data, server = self.s.recvfrom(4096)
                        except socket.error as e:
                            if e.errno != errno.EINTR:
                                raise
                        else:
                            break
                    self.response.decode(data)
                    return self.response
                except seqnum_error as e:
                    print 'seqnum error, reread', payload, function, str(e), time.time()
                    pass #just read again on seqnum error
                else:
                    break
        except socket.timeout as e:
            print 'timeout, func:', function, 'missed seqnum:', self.request.sequencenumber, time.time()
            raise protocol_timeout(str(e))
        except Exception as e:
            print 'other exc', self.request.sequencenumber, time.time(), str(e)
            raise protocol_error(str(e))

    def xtea_refresh_thread(self):
        while True:
            time.sleep(15)
            if self.controller_online:
                try:
                    self.set_xteakey()
                except Exception as e:
                    del self.request.xtea_key
                    try:
                        self.set_xteakey()
                        print 'xtea set'
                    except Exception as e:
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



