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

itemList=[]

class alarmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)
        for key, value in self.conf.iteritems():
            itemList.append({'name':key, 'value':value, 'min':0, 'max':100, 'unit':'', 'type':'R/W'})

    def getItem(self, item):
        for i in itemList:
            if i['name'] == item:
                return i['value']

    def setItem(self, item, value):
        for i in itemList:
            if i['name'] == item:
                i['value'] = value
                return 'OK'
        return['error']

    def getDataBase(self):
        l=[]
        for item in itemList:
            l.append(item['name'])
        return l

    def GetFullDB(self, tags):
        return itemList
