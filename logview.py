import cherrypy
import ConfigParser
from mako.template import Template
from mako.lookup import TemplateLookup

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
        lines = f.readlines()
        tmpl = lookup.get_template("loglines.html")
        return tmpl.render(lines=lines)
        
parser = ConfigParser.ConfigParser()


