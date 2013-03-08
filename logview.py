import os
import cherrypy
import ConfigParser
from mako.template import Template
from mako.lookup import TemplateLookup
from itertools import islice

#Look for temlates in this directory
lookup = TemplateLookup(directories=['html'])

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
        lines = islice(reversed_lines(f), 100):        
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
