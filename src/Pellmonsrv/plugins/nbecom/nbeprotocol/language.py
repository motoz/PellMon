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

import os


langfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'language', 'lang.uk.prop')

lang = dict([l.split('=') for l in open(langfile)])

def event_text(code):
    try:
        return lang[lang['setup_%s'%code].rstrip()].rstrip()
    except KeyError:
        return code

def state_text(code):
    try:
        return lang['state_%s'%code].rstrip()
    except KeyError:
        return code

def substate_text(code):
    try:
        return lang['lng_substate_%s'%code].rstrip()
    except KeyError:
        return code

customtexts = {'off_on_alarm' : lambda x:{'0':'Off', '1':'On', '2':'Alarm'}[x]
              }
