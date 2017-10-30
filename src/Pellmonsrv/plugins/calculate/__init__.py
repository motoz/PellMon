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

from Pellmonsrv.plugin_categories import protocols
from Pellmonsrv.database import Item, Getsetitem
from threading import Thread, Timer
from os import path
import os, grp, pwd
from logging import getLogger
import traceback
from time import sleep
from string import maketrans

logger = getLogger('pellMon')

itemList=[]
itemTags={}
itemValues={}
gstore = {}

class Calc():
    def __init__(self, prog, db, stack=None):
        calc = []
        for row in prog.splitlines():
          calc += row.split(' ')
        self.calc = [value for value in calc if value !='']
        self.IP = 0
        if stack == None:
            self.stack = []
        else:
            self.stack = stack
        self.db = db
        self.store = {}

    def execute(self):
        try:
            c = self.calc[self.IP]
        except:
            raise ValueError('Expected operand')
        if c=='/':
            q = float(self.stack.pop())
            d = float(self.stack.pop())
            self.stack.append(unicode(d/q))
        elif c == '*':
            d = float(self.stack.pop())
            q = float(self.stack.pop())
            self.stack.append(unicode(d*q))
        elif c=='+':
            d = float(self.stack.pop())
            q = float(self.stack.pop())
            self.stack.append(unicode(d+q))
        elif c=='-':
            d = float(self.stack.pop())
            q = float(self.stack.pop())
            self.stack.append(unicode(q-d))
        elif c=='get':
            item = self.stack.pop()
            value = self.db.get_value(item)
            self.stack.append(value)
        elif c=='set':
            item = self.stack.pop()
            value = self.stack.pop()
            result = self.db.set_value(item, value)
            self.stack.append(result)
        elif c=='>':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(float(item1) > float(item2))))
        elif c=='<':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(float(item1) < float(item2))))
        elif c=='==':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(float(item1) == float(item2))))
        elif c=='!=':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(float(item1) != float(item2))))
        elif c=='?':
            itemFalse = self.stack.pop()
            itemTrue = self.stack.pop()
            itemCheck = int(self.stack.pop())
            if itemCheck:
                self.stack.append(itemTrue)
            else:
                self.stack.append(itemFalse)
        elif c=='exec':
            name = self.stack.pop()
            calc = self.db.get_value(name)
            prog = Calc(calc, self.db, stack=self.stack)
            prog.run()
        elif c=='pop':
            self.stack.pop()
        elif c == 'dup':
            self.stack.append(self.stack[-1])
        elif c == 'sp':
            self.stack.append(len(self.stack))
        elif c == 'swap':
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            self.stack.append(item1)
            self.stack.append(item2)
        elif c=='max':
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            if float(item1) > float(item2):
                self.stack.append(item1)
            else:
                self.stack.append(item2)
        elif c=='min':
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            if float(item1) < float(item2):
                self.stack.append(item1)
            else:
                self.stack.append(item2)
        elif c == 'sto':
            var = unicode(self.stack.pop())
            self.store[var] = self.stack.pop()
        elif c == 'del':
            var = unicode(self.stack.pop())
            if self.store.has_key(var):
                del gstore[var]
        elif c == 'def':
            var = unicode(self.stack.pop())
            value = self.stack.pop()
            if not self.store.has_key(var):
                self.store[var] = value
        elif c == 'rcl':
            var = unicode(self.stack.pop())
            try:
                self.stack.append(self.store[var])
            except:
                raise ValueError('no variable named %s'%var)
        elif c == 'gsto':
            var = unicode(self.stack.pop())
            gstore[var] = self.stack.pop()
        elif c == 'gdef':
            var = unicode(self.stack.pop())
            value = self.stack.pop()
            if not gstore.has_key(var):
                gstore[var] = value
        elif c == 'gdel':
            var = unicode(self.stack.pop())
            if gstore.has_key(var):
                del gstore[var]
        elif c == 'grcl':
            try:
                var = unicode(self.stack.pop())
                self.stack.append(gstore[var])
            except:
                raise ValueError('no global named %s'%var)
        elif c == 'str==':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(str(item1) == str(item2))))
        elif c == 'str!=':
            item2 = self.stack.pop()
            item1 = self.stack.pop()
            self.stack.append(unicode(int(str(item1) != str(item2))))
        else:
            self.stack.append(c)
        self.IP += 1

    def next(self):
        try:
            if self.IP == len(self.calc):
                return 'STOP'
            else:
                return self.calc[self.IP]
        except:
            raise ValueError('Operand expected')

    def skip(self, stop_on):
        try:
            while not self.next() in stop_on:
                if self.next() == 'if':
                    self.IP += 1
                    self.skip(('end',))
                self.IP += 1
        except:
            raise ValueError('missing %s'%('|').join(stop_on))

    def run(self, stop_on = ('STOP',)):
        try:
            while not self.next() in stop_on: 
                if self.next() == 'if':
                    self.IP += 1
                    self.run(('then',))
                    result = self.stack.pop()
                    if int(result):
                        self.IP += 1
                        self.run(('end','else'))
                        if self.next() == 'else':
                            self.skip(('end',))
                        self.IP += 1
                    else:
                        self.IP += 1
                        self.skip(('end','else'))
                        if self.next() == 'else':
                            self.IP += 1
                            self.run(('end',))
                        self.IP += 1
                else:
                    self.execute()
            try:
                return self.stack[-1]
            except IndexError:
                raise IndexError('No return value, stack is empty')
        except Exception as e:
            if self.IP < len(self.calc):
                raise ValueError("'%s' at %u: %s "%(self.calc[self.IP], self.IP, str(e)))
            else:
                if stop_on != ('STOP',):
                     raise ValueError('missing %s'%('|').join(stop_on)) 
                raise ValueError('unexpected end of program, %s at %u'%(str(e),self.IP))


class calculateplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.calc2index={}
        self.name2index={}
        self.tasks = {}
        self.itemrefs = []
        try:
            for key, value in self.conf.iteritems():
                try:
                    calc_name = key.split('_')[0]
                    calc_data = key.split('_')[1]

                    if not self.calc2index.has_key(calc_name):
                        itemList.append({'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})
                        self.calc2index[calc_name] = len(itemList)-1

                    if calc_data == 'prog':
                        itemList[self.calc2index[calc_name]]['name'] = key 
                        value = value.decode('utf-8')
                        value = value.translate({ord(u'\t'):u' ', ord(u'\n'):u' '})
                        itemList[self.calc2index[calc_name]]['value'] = value
                        #itemList[self.calc2index[calc_name]]['type'] = 'R/W' 
                        self.name2index[key] = self.calc2index[calc_name]
                        itemTags[key] = ['All', 'Calculate']

                    elif calc_data == 'readitem':
                        itemList.append({'name':value, 'value':'', 'calc_item':calc_name+'_prog', 'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})  
                        itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'', 'type':'R', 'description':'Contains the item name to read to execute %s and retrieve the result'%calc_name})  
                        itemTags[value] = ['All', 'Calculate', 'Basic']
                        itemTags[key] = ['All', 'Calculate']
                        self.name2index[value]=len(itemList)-2
                        self.name2index[key]=len(itemList)-1

                    elif calc_data == 'readwriteitem':
                        itemList.append({'name':value, 'value':'', 'calc_item':calc_name+'_prog','min':'', 'max':'', 'unit':'', 'type':'R/W', 'description':''})
                        itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'','type':'R', 'description':'Contains the item name to read to execute %s and retrieve the result'%calc_name})
                        itemTags[value] = ['All', 'Calculate', 'Basic']                                                                                  
                        itemTags[key] = ['All', 'Calculate']                                                                                             
                        self.name2index[value]=len(itemList)-2                                                                                           
                        self.name2index[key]=len(itemList)-1

                    elif calc_data == 'writeitem':
                        itemList.append({'name':value, 'value':'', 'calc_item':calc_name+'_prog','min':'', 'max':'', 'unit':'', 'type':'W', 'description':''})
                        itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'','type':'R', 'description':'Contains the item name to read to execute %s and retrieve the result'%calc_name})
                        itemTags[value] = ['All', 'Calculate', 'Basic']                                                                                  
                        itemTags[key] = ['All', 'Calculate']                                                                                             
                        self.name2index[value]=len(itemList)-2                                                                                           
                        self.name2index[key]=len(itemList)-1

                    elif calc_data == 'progtype':
                        if value in ['R','R/W']:
                            itemList[self.calc2index[calc_name]]['type'] = value
                        else:
                           raise ValueError('unknown type %s in %s'%(value, key)) 

                    elif calc_data == 'taskcycle':
                        try:
                            taskcycle = float(value)
                            self.tasks[calc_name] = calcthread(taskcycle, calc_name+'_prog', self)
                        except Exception, e:
                            raise e #ValueError('%s has invalid task time %s'%(key, value))

                except Exception,e: 
                    logger.info(str(e))
                    raise e
            for item in itemList:
                if item['type'] == 'R/W':
                    self.store_setting(item['name'], confval = item['value'])
                else:
                    itemValues[item['name']] = item['value']

            self.migrate_settings('calculate')

            for item in itemList:
                dbitem = Getsetitem(item['name'], None, lambda i:self.getItem(i), lambda i,v:self.setItem(i,v))
                for key, value in item.iteritems():
                    if key != 'value':
                        dbitem.__setattr__(key, value)
                if dbitem.name in itemTags:
                    dbitem.__setattr__('tags', itemTags[dbitem.name])
                self.db.insert(dbitem)
                self.itemrefs.append(dbitem)

        except Exception, e:
            logger.info( str(e))
            raise

    def getItem(self, itemName):
        if self.name2index.has_key(itemName):
            item = itemList[self.name2index[itemName]]
            try:
                calc_item = item['calc_item']
                if item['type'] in ['R','R/W']:
                    prog = self.getItem(calc_item)
                    try:
                        calc = Calc(prog, self.db)
                        return calc.run()
                    except Exception, e:
                        logger.info(calc_item+' error: '+repr(e))
                        return 'error'
            except:
                if item['type'] == 'R':
                    return item['value']
                else:
                    try:
                        value = self.load_setting(itemName)
                        return value
                    except:
                        return 'error'
        else:
            return 'error'

    def setItem(self, itemname, value):
        try:
            item = itemList[self.name2index[itemname]]
            calc_item = item['calc_item']
            prog = self.getItem(calc_item)
            try:
                stack = [unicode(value)]
                calc = Calc(prog, self.db, stack=stack)
                calc.run()
                return 'OK'
            except Exception, e:
                calc = Calc(prog, self.db)
                logger.info(calc_item+' error: '+str(e))
                return 'error'
        except:  
            try:
                item = itemList[self.name2index[itemname]]
                if item['type'] == 'R/W':
                    self.store_setting(item['name'], value)
                    return 'OK'
            except Exception,e:
                return 'error'

class calcthread(Thread):
    def __init__(self, cycle, progitem, plugin_object):
        Thread.__init__(self)
        self.cycle = cycle
        self.setDaemon(True)
        self.progitem = progitem
        self.plugin_object = plugin_object
        self.start()
    def run(self):
        while True:
            try:
                prog = Calc(self.plugin_object.getItem(self.progitem), self.plugin_object.db)
                prog.run()
            except Exception as e:
                logger.info('error in ' + self.progitem +str(e))
            sleep(self.cycle)
