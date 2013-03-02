#! /usr/bin/python
# -*- encoding: UTF-8 -*-
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

import os.path
import cherrypy
from cherrypy.lib.static import serve_file
import ConfigParser
from mako.template import Template
from mako.lookup import TemplateLookup
from cherrypy.lib import caching
import dbus
from auth import AuthController, require, member_of, name_is
import simplejson

#Look for temlates in this directory
lookup = TemplateLookup(directories=['html'])

parser = ConfigParser.ConfigParser()

# Load the configuration file
parser.read('pellmon.conf')

# The RRD database, updated by pellMon
db = parser.get('conf', 'database') 

# And the colors to use when drawing the graph
colors = parser.items('graphcolors')
colorsDict = {}
for key, value in colors:
    colorsDict[key] = value
    
# Get the names of the polled data 
polldata = parser.items("pollvalues")

timeChoices = ['time1h', 'time3h', 'time8h', 'time24h', 'time3d', 'time1w']
timeNames  = ['1 hour', '3 hours', '8 hours', '24 hours', '3 days', '1 week']
timeSeconds = [3600, 3600*3, 3600*8, 3600*24, 3600*24*3, 3600*24*7]    

class PellMonWebb:

    auth = AuthController()
    
    @cherrypy.expose
    def form1(self, **args):
        # The checkboxes are submitted with 'post'
        if cherrypy.request.method == "POST": 
            # put the selection in session
            for key,val in polldata:
                # is this dataset checked?
                if args.has_key(val):
                    # if so, set it in the session
                    cherrypy.session[val] = 'yes'
                else:
                    cherrypy.session[val] = 'no' 
            
            if args.has_key('autorefresh'):
                cherrypy.session['autorefresh']='yes'
            else:
                cherrypy.session['autorefresh']='no'
        # redirect back after setting selection in session
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def form2(self, **args):
        # The radiobuttons are submitted with 'post'
        if cherrypy.request.method == "POST": 
            if args.has_key('graphtime') and args.get('graphtime') in timeChoices:
                cherrypy.session['timeChoice']=args.get('graphtime')
        # redirect back after setting selection in session
        raise cherrypy.HTTPRedirect('/')
        
    @cherrypy.expose
    def left(self, **args):
        if not cherrypy.session.get('time'):
            cherrypy.session['time'] = '0'
        if not cherrypy.session.get('timeChoice'):
            cherrypy.session['timeChoice'] = 'time1h'
        if cherrypy.request.method == "POST": 
            seconds=timeSeconds[timeChoices.index(cherrypy.session['timeChoice'])]
            cherrypy.session['time']=str(int(cherrypy.session['time'])+seconds)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(title="Hello"))
        # redirect back after setting selection in session
        #raise cherrypy.HTTPRedirect('/')        

    @cherrypy.expose
    def right(self, **args):
        if not cherrypy.session.get('time'):
            cherrypy.session['time'] = '0'
        if not cherrypy.session.get('timeChoice'):
            cherrypy.session['timeChoice'] = 'time1h'
        if cherrypy.request.method == "POST": 
            seconds=timeSeconds[timeChoices.index(cherrypy.session['timeChoice'])]
            time=int(cherrypy.session['time'])-seconds
            if time<0:
                time=0
            cherrypy.session['time']=str(time)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(title="Hello, %s" % name))
        # redirect back after setting selection in session
        #raise cherrypy.HTTPRedirect('/')    
                
    @cherrypy.expose
    def image(self, **args):
        if not cherrypy.session.get('timeChoice'):
            cherrypy.session['timeChoice'] = 'time1h'
        if not cherrypy.session.get('time'):
            cherrypy.session['time'] = '0'          
        graphTime = timeSeconds[timeChoices.index(cherrypy.session.get('timeChoice'))]
        offset = int(cherrypy.session['time'])
        graphTimeStart=str(graphTime + offset)
        graphTimeEnd=str(offset)
        #Build the command string to make a graph from the database         
        RrdGraphString1="rrdtool graph "+os.getcwd()+"/graph1.png --lower-limit 0 --right-axis 1:0 --width 700 --height 400 --end now-"+graphTimeEnd+"s --start now-"+graphTimeStart+"s "
        for key,value in polldata:
            if cherrypy.session.get(value)=='yes':
                RrdGraphString1=RrdGraphString1+"DEF:%s="%key+db+":%s:AVERAGE LINE1:%s%s:\"%s\" "% (value, key, colorsDict[key], value) 
        RrdGraphString1=RrdGraphString1+">>/dev/null"   
        os.system(RrdGraphString1)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return serve_file(os.getcwd()+'/graph1.png', content_type='image/png')

    @cherrypy.expose
    @require() #requires valid login
    def getparam(self, param):
        parameterlist=getdb()
        if cherrypy.request.method == "GET": 
            if param in(parameterlist): 
                try:
                    result = getItem(param)
                except:
                    result = 'error'
            else: result = 'not found'
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(dict(param=param, value=result))

    @cherrypy.expose
    @require() #requires valid login
    def setparam(self, param, data=None):
        parameterlist=getdb()
        if cherrypy.request.method == "POST": 
            if param in(parameterlist): 
                try:
                    result = setItem(param, data)
                except:
                    result = 'error'
            else: result = 'not found'
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(dict(param=param, value=result))
        
    @cherrypy.expose
    @require() #requires valid login
    def parameters(self, **args):
        # Get list of data/parameters 
        parameterlist=getdb()
        values=['']*len(parameterlist)
        params={}
        for item in parameterlist:
            params[item] = ' '
            if args.has_key(item):
                if cherrypy.request.method == "POST": 
                    # set parameter
                    try:
                        values[parameterlist.index(item)]=setItem(item, args[item][1])
                    except:
                        values[parameterlist.index(item)]='error'
                else:
                    # get parameter
                    try:
                        values[parameterlist.index(item)]=getItem(item)  
                    except:
                        values[parameterlist.index(item)]='error'
        tmpl = lookup.get_template("parameters.html")
        return tmpl.render(params=parameterlist, values=values)

    
    @cherrypy.expose
    def index(self, **args):
        if not cherrypy.session.get('timeChoice'):
            cherrypy.session['timeChoice']=timeChoices[0]               
        checkboxes=[] 
        empty=True
        for key, val in polldata:  
            if cherrypy.session.get(val)=='yes':  
                checkboxes.append((val,True))
                empty=False
            else:
                checkboxes.append((val,''))
        autorefresh = cherrypy.session.get('autorefresh')=='yes'
        tmpl = lookup.get_template("index.html")
        return tmpl.render(username=cherrypy.session.get('_cp_username'), checkboxes=checkboxes, empty=empty, autorefresh=autorefresh, timeChoices=timeChoices, timeNames=timeNames, timeChoice=cherrypy.session.get('timeChoice'))    

    @cherrypy.expose
    def submit(self, name):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(title="Hello"))

MEDIA_DIR = os.path.join(os.path.abspath("."), u"media")

global_conf = {
       'global':    { 'server.environment': 'debug',
                      'tools.sessions.on' : True,
                      'tools.sessions.timeout': 7200,
                      'tools.auth.on': True,
                      'engine.autoreload_on': True,
                      'engine.autoreload_frequency': 5,
                      'server.socket_host': '0.0.0.0',
                      'server.socket_port': int(parser.get('conf', 'port')),
                    }
              }
app_conf =  {'/media':
                {'tools.staticdir.on': True,
                 'tools.staticdir.dir': MEDIA_DIR}
            }              
              
# Connect to pellmonsrv on the dbus system bus
bus = dbus.SystemBus()
pelletService = bus.get_object('org.pellmon.int', '/org/pellmon/int')
getItem = pelletService.get_dbus_method('GetItem', 'org.pellmon.int')
setItem = pelletService.get_dbus_method('SetItem', 'org.pellmon.int')
getdb = pelletService.get_dbus_method('GetDB', 'org.pellmon.int')


current_dir = os.path.dirname(os.path.abspath(__file__))
cherrypy.config.update(global_conf)                        
cherrypy.quickstart(PellMonWebb(), config=app_conf)
                 
                 
                 
