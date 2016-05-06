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
from Pellmonsrv.yapsy.IPlugin import IPlugin
from ConfigParser import ConfigParser
import os
from logging import getLogger
from database import Keyval_storage

logger = getLogger('pellMon')

class protocols(IPlugin):
    """This is the interface for plugins of class protocols"""
    def activate(self, conf, glob, db, datadir):
        # Save globals for plugin access to everything
        self.glob = glob
        self.conf = conf
        self.db = db
        self.datadir = datadir
        self.templates = {}
        IPlugin.activate(self)

    def _insert_template(self, name, template):
        self.templates[name] = template

    def getItem(self, item):
        """Return the value for one item"""
        return 'valuestring'

    def setItem(self, item, value):
        """Set the value of one item"""
        return 'ok'

    def sendmail(self, msg):
        """Callback to send mail message"""
        glob['sendmail'](msg)

    def settings_changed(self, item, oldvalue, newvalue, itemtype='parameter'):
        """Callback from plugin when a changed setting value is detected"""
        self.glob['handle_settings_changed'](item, oldvalue, newvalue, itemtype)

    def getMenutags(self):
        return []

    def getTemplate(self, template):
        try:
            return self.templates[template]
        except KeyError:
            return None

    def load_setting(self, item):
        return Keyval_storage.keyval_storage.readval(item)

    def store_setting(self, item, value=None, confval=None):
        Keyval_storage.keyval_storage.writeval(item, value, confval)

    def migrate_settings(self, plugin):
        """This is used to migrate settings from the old values.conf text files
        to the new sqlite database"""
        oldsettings = ConfigParser()
        try:
            oldfile = os.path.join(self.glob['conf'].old_plugin_dir, plugin, 'values.conf')
            if os.path.isfile(oldfile):
                oldsettings.read(oldfile)
                for key, value in oldsettings.items('values'):
                    self.store_setting(key, value)
                os.rename(oldfile, oldfile + '.migrated')
                logger.info('migrated settings from %s plugin to settings database'%plugin)
        except Exception, e:
            logger.info('migration of old %s plugin settings failed'%plugin)

