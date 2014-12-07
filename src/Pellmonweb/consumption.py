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
from os import path
import cherrypy
from mako.lookup import TemplateLookup

lookup = TemplateLookup(directories=[path.join(path.dirname(__file__), 'html')])

class Consumption(object):
    def __init__(self, polling, db, dbus):
        self.dbus = dbus
        self.polling=polling

    @cherrypy.expose
    def consumption(self):
        if not self.polling:
            return ""
        tmpl = lookup.get_template("consumption.html")
        return tmpl.render(username=cherrypy.session.get('_cp_username'), webroot=cherrypy.request.script_name)

    @cherrypy.expose
    def flotconsumption24h(self, **args):
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return self.dbus.getItem('consumptionData24h')

    @cherrypy.expose
    def flotconsumption7d(self, **args):
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return self.dbus.getItem('consumptionData7d')

    @cherrypy.expose
    def flotconsumption8w(self):
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return self.dbus.getItem('consumptionData8w', **args)

    @cherrypy.expose
    def flotconsumption1y(self, **args):
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return self.dbus.getItem('consumptionData1y')

