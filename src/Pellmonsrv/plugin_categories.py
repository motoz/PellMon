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

class protocols(IPlugin):
    """This is the interface for plugins of class protocols"""
    def activate(self, conf, glob):
        # Save globals for plugin access to everything
        self.glob = glob
        self.conf = conf
        IPlugin.activate(self)

    def getItem(self, item):
        """Return the value for one item"""
        return 'valuestring'

    def setItem(self, item, value):
        """Set the value of one item"""
        return 'ok'

    def getDataBase(self):
        """Return a list of item names"""
        return []

    def GetFullDB(self, tags):
        """Return a list of dictionarys, each dictionary contains at least
        'name':'item_name', 'type':'R|R/W|W'
        and optionally 
        'min', 'max', 'unit', 'longname', 'description' keys with string type values"""
        return [{}]

    def sendmail(self, msg):
        """Callback to send mail message"""
        glob['sendmail'](msg)

    def settings_changed(self, item, oldvalue, newvalue, itemtype='parameter'):
        """Callback from plugin when a changed setting value is detected"""
        self.glob['handle_settings_changed'](item, oldvalue, newvalue, itemtype)

    def getMenutags(self):
        return []
