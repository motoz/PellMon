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
import ConfigParser
from mako.template import Template
from mako.lookup import TemplateLookup
from itertools import islice

#Look for temlates in this directory
lookup = TemplateLookup(directories=['web/html'])

# Load the configuration file
parser = ConfigParser.ConfigParser()
parser.read('pellmon.conf')        

logfile=parser.get('conf', 'logfile')


class LogViewer(object):    
    @cherrypy.expose
    def logView(self):
        tmpl = lookup.get_template("logview.html")
        return tmpl.render()
    
    @cherrypy.expose
    def getlines(self):    
        f = open(logfile, "r")
        #lines = f.readlines()
        lines = islice(reversed_lines(f), 100)        
        tmpl = lookup.get_template("loglines.html")
        return tmpl.render(lines=lines)
        
parser = ConfigParser.ConfigParser()

def reversed_lines(file):
    "Generate the lines of file in reverse order."
    part = ''
    for block in reversed_blocks(file):
        for c in reversed(block):
            if c == '\n' and part:
                yield part[::-1]
                part = ''
            part += c
    if part: yield part[::-1]

def reversed_blocks(file, blocksize=4096):
    "Generate blocks of file's contents in reverse order."
    file.seek(0, os.SEEK_END)
    here = file.tell()
    while 0 < here:
        delta = min(blocksize, here)
        file.seek(here - delta, os.SEEK_SET)
        yield file.read(delta)
        here -= delta
