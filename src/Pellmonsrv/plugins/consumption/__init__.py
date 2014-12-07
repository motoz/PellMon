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
import time
from datetime import datetime
from logging import getLogger
from time import mktime
from datetime import datetime
import subprocess
import simplejson as json
import re
import math
import random

logger = getLogger('pellMon')

itemList=[{'name':'consumptionData24h',  'longname':'Consumption 24 hours',
           'type':'R',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'-'},
          {'name':'consumptionData7d',  'longname':'Consumption 7 days',
           'type':'R',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'-'},
          {'name':'consumptionData4w',  'longname':'Consumption 4 weeks',
           'type':'R',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'-'},
          {'name':'consumptionData1y',  'longname':'Consumption 1 year',
           'type':'R',   'unit':'kg'   ,   'value':'0', 'min':'0', 'max':'-'},
         ]


class silolevelplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob):
        protocols.activate(self, conf, glob)

    def getItem(self, itemName):
        return 123

    def getDataBase(self):
        return [item['name'] for item in itemList]

