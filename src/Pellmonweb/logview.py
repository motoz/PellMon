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
import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
from itertools import islice
from cgi import escape
from datetime import datetime

lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'html')])

class LogViewer(object):    
    def __init__(self, logfile):
        self.logfile = logfile
    
    @cherrypy.expose
    def logView(self):
        #Look for temlates in this directory
        tmpl = lookup.get_template("logview.html")
        return tmpl.render(username = cherrypy.session.get('_cp_username'))
    
    @cherrypy.expose
    def getlines(self, linenum=100):    
        fmt = '%Y-%m-%d %H:%M:%S'
        f = open(self.logfile, "r")
        try:
            ln=int(linenum)
            lines = islice(reversed_lines(f), ln)
            timelines = []
            for line in lines:
                try:
                    time = datetime.strptime(line[:19], fmt)
                    seconds = str(int((time-datetime(1970,1,1)).total_seconds()))
                except:
                    seconds = None
                timelines.append((seconds, line))
            tmpl = lookup.get_template("loglines.html")
            return tmpl.render(lines=timelines)
        except Exception,e:
            return str(e)

def reversed_lines(file):
    "Generate the lines of file in reverse order."
    part = ''
    for block in reversed_blocks(file):
        for c in reversed(block):
            if c == '\n' and part:
                yield escape(part[::-1])
                part = ''
            part += c
    if part: yield escape(part[::-1])

def reversed_blocks(file, blocksize=4096):
    "Generate blocks of file's contents in reverse order."
    file.seek(0, os.SEEK_END)
    here = file.tell()
    while 0 < here:
        delta = min(blocksize, here)
        file.seek(here - delta, os.SEEK_SET)
        yield file.read(delta)
        here -= delta
