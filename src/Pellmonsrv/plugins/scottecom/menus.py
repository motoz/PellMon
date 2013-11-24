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
from datamenu import dataBaseTags

Menutags = ['Overview', 'Blower', 'Ignition', 'Feeder', 'Oxygen', 'Timer', 'Cleaning', 'Temps'] 
Tags = ['Basic', 'All', 'Settings', 'Measurements']
Alltags = Tags+Menutags

def getDbWithTags(wantedtags):
    params=[]
    for param, tags in dataBaseTags.iteritems():
        paramtags=[]
        for i in range(0,len(tags)):
            if tags[i]=='X':
                paramtags.append(Alltags[i])
        accepted=True
        for tag in wantedtags:
            if tag=='':
                break;
            if not tag in paramtags:
                accepted=False
        if accepted:
            params.append(param)
    return params

def getMenutags():
    return Menutags
