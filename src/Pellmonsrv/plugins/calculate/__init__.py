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
from threading import Thread, Timer
from ConfigParser import ConfigParser
from os import path
import os, grp, pwd

itemList=[]
itemTags={}
itemValues={}
Menutags = ['Calculate']

class calculateplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)

        for key, value in self.conf.iteritems():
            try:
                calc_name = key.split('_')[0]
                calc_data = key.split('_')[1]
                if calc_data == 'calc':
                    itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'', 'type':'R/W', 'description':''})           
                elif calc_data == 'read':
                    itemList.append({'name':key, 'value':value, 'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})       
                    itemList.append({'name':value, 'value':'', 'calc_item':calc_name+'_calc', 'min':'', 'max':'', 'unit':'', 'type':'R', 'description':''})  
                    itemTags[value] = ['All', 'Calculate', 'Basic']       
                itemTags[key] = ['All', 'Calculate', 'Basic']
                itemTags[key].append(calc_name)
            except Exception,e: 
                print e
        self.valuestore = ConfigParser()
        self.valuestore.add_section('values')
        self.valuesfile = path.join(path.dirname(__file__), 'values.conf')
        for item in itemList:
            if item['type'] == 'R/W':
                self.valuestore.set('values', item['name'], item['value'])
            else:
                itemValues[item['name']] = item['value']
        self.valuestore.read(self.valuesfile)
        f = open(self.valuesfile, 'w')
        self.valuestore.write(f)
        f.close()
        try:
            uid = pwd.getpwnam(self.glob['conf'].USER).pw_uid
            gid = grp.getgrnam(self.glob['conf'].GROUP).gr_gid
            os.chown(self.valuesfile, uid, gid)
        except:
            pass
            
    def execute(self, itemName, stack=[]):
        try:
            calc = self.getItem(itemName)
            for c in calc.split(';'):
                if c=='DIV':
                    q = float(stack.pop())
                    d = float(stack.pop())
                    stack.append(str(d/q))
                elif c=='MUL':
                    d = float(stack.pop())
                    q = float(stack.pop())
                    stack.append(str(d*q))
                elif c=='ADD':
                    d = float(stack.pop())
                    q = float(stack.pop())
                    stack.append(str(d+q))
                elif c=='SUB':
                    d = float(stack.pop())
                    q = float(stack.pop())
                    stack.append(str(q-d))
                elif c=='GET':
                    item = stack.pop()
                    value = self.glob['conf'].database.items[item].getItem()
                    stack.append(value)   
                elif c=='SET':
                    item = stack.pop()
                    value = stack.pop()
                    result = self.glob['conf'].database.items[item].setItem(value)
                    stack.append(result)   
                elif c=='>':
                    item2 = stack.pop()
                    item1 = stack.pop()
                    stack.append(str(int(item1 > item2)))   
                elif c=='<':
                    item2 = stack.pop()
                    item1 = stack.pop()
                    stack.append(str(int(item1 < item2)))  
                elif c=='==':
                    item2 = stack.pop()
                    item1 = stack.pop()
                    stack.append(str(int(item1 == item2)))  
                elif c=='!=':
                    item2 = stack.pop()
                    item1 = stack.pop()
                    stack.append(str(int(item1 != item2))) 
                elif c=='IF':
                    itemFalse = stack.pop()
                    itemTrue = stack.pop()
                    itemCheck = int(stack.pop())
                    if itemCheck:
                        stack.append(itemTrue)
                    else:
                        stack.append(itemFalse)   
                elif c=='EXEC':
                    calc_item = stack.pop()
                    stack.append(self.execute(calc_item, stack))   
                elif c=='POP':
                    stack.pop()
                else:
                    stack.append(c)
            return stack.pop() 
        except:
            return 'error'
        
    def getItem(self, itemName):
        for i in itemList:
            if i['name'] == itemName:
                item = i
                try:
                    calc_item = item['calc_item']
                    return self.execute(calc_item)
                except:
                    try:
                        return str(itemValues[itemName])
                    except:
                        try:
                            value = self.valuestore.get('values', itemName)
                            return value
                        except:
                            return 'error'

    def setItem(self, item, value):
        try:
            if itemValues.has_key(item):
                itemValues[item] = value
                return 'OK'
            else:
                self.valuestore.set('values', item, str(value))
                f = open(self.valuesfile, 'w')
                self.valuestore.write(f)
                f.close()
                return 'OK'
        except Exception,e:
            return 'error'

    def getDataBase(self):
        l=[]
        for item in itemList:
            l.append(item['name'])
        return l

    def GetFullDB(self, tags):

        def match(requiredtags, existingtags):
            for rt in requiredtags:
                if rt != '' and not rt in existingtags:
                    return False
            return True
            
        items = [item for item in itemList if match(tags, itemTags[item['name']]) ]
        items.sort(key = lambda k:k['name'])
        return items
        
    def getMenutags(self):
        return Menutags
        t = Timer(5, self.poll_thread)
        t.setDaemon(True)
        t.start()
