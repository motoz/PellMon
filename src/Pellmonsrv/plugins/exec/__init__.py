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
from Pellmonsrv.database import Cacheditem
from logging import getLogger
import subprocess

logger = getLogger('pellMon')

class execplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []

        config = {}
        for index_key, value in self.conf.items():
            if '_' in index_key:
                index, key = index_key.split('_')
                try:
                    config[index][key] = value
                except KeyError:
                    config[index] = {key:value}
        for index, itemconf in config.items():
            try:
                itemname = itemconf.pop('item')
                itemvalue = itemconf.pop('value', '0')
                readscript = itemconf.pop('readscript', None);
                writescript = itemconf.pop('writescript', None);
                try:
                    cachetime = float(itemconf.pop('cachetime', '0'))
                except:
                    cachetime = 0

                getter = None
                setter = None
                itemtype = 'R'
                if readscript:
                    if writescript:
                        itemtype = 'R/W'
                    getter = lambda item, script=readscript:self.execute_readscript(item, script)
                else:
                    if writescript:
                        itemtype = 'W'
                if writescript:
                    self.writescript = writescript
                    setter = lambda item, value, script=writescript:self.execute_writescript(item, value, script)

                item = Cacheditem(itemname, itemvalue, getter=getter, setter=setter, timeout=cachetime)

                for key, value in itemconf.items():
                    setattr(item, key, value)

                item.tags = itemconf.pop('tags', 'All Basic Exec').split(' ')
                item.type = itemtype
                item.min = itemconf.pop('min', '')
                item.max = itemconf.pop('max', '')
                self.db.insert(item)
                self.itemrefs.append(item)

            except Exception, e:
                logger.info('Exec plugin config error: %s', str(e))
                raise

    def execute_readscript(self, item, script):
        try:
            return subprocess.check_output(script, shell=True)
        except CalledProcessError:
            return 'error'

    def execute_writescript(self, item, value, script):
        try:
            command, script = script.split(' ', 1)
            parameters = script.format(value).split(' ')
            subprocess.check_call([command]+parameters, shell=False)
            return 'ok'
        except subprocess.CalledProcessError as e:
            return 'error'


