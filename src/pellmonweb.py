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

import os.path
import cherrypy
from cherrypy.lib.static import serve_file, serve_fileobj
from cherrypy.process import plugins, servers
import ConfigParser
from mako.template import Template
from mako.lookup import TemplateLookup
from cherrypy.lib import caching
from gi.repository import Gio, GLib, GObject
import simplejson
import threading, Queue
from Pellmonweb import *
from time import mktime
import time
import threading
import sys
from Pellmonweb import __file__ as webpath
import argparse
import pwd
import grp
import subprocess
from datetime import datetime
from cgi import escape
from threading import Timer
import signal

try:
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from ws4py.websocket import WebSocket
    websockets = True
except:
    websockets = False
    print 'ws4py module is missing, install with "pip install ws4py" for websocket support'

class Sensor(object):
    sensorlist = []
    def __init__(self, parameters, websocket, events):
        self.websocket = websocket
        self.params = parameters
        self.db = {k:'-' for k in self.params}
        self.events = events
        Sensor.sensorlist.append(self)
        paramlist = []
        for param in self.params:
            try:
                value = dbus.getItem(param)
                if value != self.db[param]:
                    paramlist.append(dict(name=param, value=value))
            except Exception, e:
                print str(e)
                pass
        try:
            if paramlist:
                message = simplejson.dumps(paramlist)
                t = Timer(1, self.websocket.send, args= [message])
                t.start()
            for p in paramlist:
                self.db[p['name']] = p['value']
        except Exception, e:
            self.websocket = None

    def send(self, message):
        try:
            paramlist = []
            for param in message:
                if param['name'] in self.params or (param['name'] == '__event__' and self.events):
                    paramlist.append(param)
            try:
                if paramlist:
                    message = simplejson.dumps(paramlist)
                    self.websocket.send(message)
                return True
            except Exception, e:
                self.websocket = None
                return False

            ml = []
            ml.append(message)
            message = simplejson.dumps(ml)
            self.websocket.send(message)
            return True
        except Exception, e:
            self.websocket = None
            return False

class DbusNotConnected(Exception):
    pass

class Dbus_handler:
    def __init__(self, bus='SESSION'):
        if bus=='SYSTEM':
            self.bustype=Gio.BusType.SYSTEM
        else:
            self.bustype=Gio.BusType.SESSION

    def start(self):
        self.notify = None
        self.bus = Gio.bus_get_sync(self.bustype, None)
        Gio.bus_watch_name(
            self.bustype,
            'org.pellmon.int',
            Gio.DBusProxyFlags.NONE,
            self.dbus_connect,
            self.dbus_disconnect,
        )

    def dbus_connect(self, connection, name, owner):
        self.notify = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            'org.pellmon.int',
            '/org/pellmon/int',
            'org.pellmon.int',
            None)
        def on_signal(proxy, sender_name, signal_name, parameters):
            p = parameters[0]
            for i in xrange(len(Sensor.sensorlist) - 1, -1, -1):
                sensor = Sensor.sensorlist[i]
                if not sensor.send(p):
                    del Sensor.sensorlist[i]
            #if signal_name == "MediaPlayerKeyPressed":
            #    self._key_pressed(*parameters)
        self.notify.connect("g-signal", on_signal)


    def dbus_disconnect(self, connection, name):
        if self.notify:
            self.notify = None


    def getItem(self, itm):
        if self.notify:
            return self.notify.GetItem('(s)',itm)
        else:
            raise DbusNotConnected("server not running")

    def setItem(self, item, value):
        if self.notify:
            return self.notify.SetItem('(ss)',item, value)
        else:
            raise DbusNotConnected("server not running")

    def getdb(self):
        if self.notify:
            return self.notify.GetDB()
        else:
            raise DbusNotConnected("server not running")

    def getDBwithTags(self, tags):
        if self.notify:
            return self.notify.GetDBwithTags('(as)',tags)
        else:
            raise DbusNotConnected("server not running")

    def getFullDB(self, tags):
        if self.notify:
            db = self.notify.GetFullDB('(as)', tags)
            return db
        else:
            raise DbusNotConnected("server not running")

    def getMenutags(self):
        if self.notify:
            return self.notify.getMenutags()
        else:
            raise DbusNotConnected("server not running")

class PellMonWeb:
    def __init__(self):
        self.logview = LogViewer(logfile)
        self.auth = AuthController(credentials)
        self.consumptionview = Consumption(polling, db)

    @cherrypy.expose
    def autorefresh(self, **args):
        if cherrypy.request.method == "POST":
            if args.has_key('autorefresh') and args.get('autorefresh') == 'yes':
                cherrypy.session['autorefresh'] = 'yes'
            else:
                cherrypy.session['autorefresh'] = 'no'
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(enabled=cherrypy.session['autorefresh']))

    @cherrypy.expose
    def graphsession(self, **args):
        if cherrypy.request.method == "POST":
            try:
                if args.has_key('width'):
                    cherrypy.session['width'] = int(args['width'])
                if args.has_key('height'):
                    cherrypy.session['height'] = int(args['height'])
                if args.has_key('timespan'):
                    cherrypy.session['timespan'] = int(args['timespan'])
                if args.has_key('timeoffset'):
                    cherrypy.session['timeoffset'] = int(args['timeoffset'])
                if args.has_key('lines'):
                    lines = args['lines'].split(',')
                    cherrypy.session['lines'] = lines
            except:
                pass
            return 'ok'

    @cherrypy.expose
    def graph(self, **args):
        if not polling:
            return None
        if len(colorsDict) == 0:
            return None

        # Set x axis time span with ?timespan=xx 
        try:
            timespan = int(args['timespan'])
        except:
            try:
                timespan = int(cherrypy.session['timespan'])
            except:
                timespan = 3600

        # Set x axis end time with ?time=xx 
        try:
            graphtime = int(args['time'])
        except:
            graphtime = int(time.time())

        # Offset x-axis with ?timeoffset=xx 
        try:
            timeoffset = int(args['timeoffset'])
        except:
            try:
                timeoffset = int(cherrypy.session['timeoffset'])
            except:
                timeoffset = 0

        # Set graph width with ?width=xx 
        try:
            graphWidth = int(args['width'])
        except:
            try:
                graphWidth = int(cherrypy.session['width'])
            except:
                graphWidth = 440 # Default bootstrap 3 grid size
        if graphWidth > 5000:
            graphWidth = 5000

        # Set graph height with ?height=xx 
        try:
            graphHeight = int(args['height'])
        except:
            try:
                graphHeight = int(cherrypy.session['height'])
            except:
                graphHeight = 400
        if graphHeight > 2000:
            graphHeight = 2000

        # Set plotlines with ?lines=line1,line2,line3
        try:
            lines = args['lines'].split(',')
        except:
            try:
                lines = cherrypy.session['lines']
            except:
                lines = '__all__'
        if graphHeight > 2000:
            graphHeight = 2000

        # Hide legends with ?legends=no
        legends = ''
        try:
            if args['legends'] == 'no':
                legends = ' --no-legend '
        except:
            pass

        # Set background color with ?bgcolor=rrbbgg (hex color)
        try:
            bgcolor =  args['bgcolor']
            if len(bgcolor) == 6:
                test = int(bgcolor, 16)
            bgcolor = ' --color BACK#'+bgcolor
        except:
            bgcolor = ' '

        # Set background color with ?bgcolor=rrbbgg (hex color)
        try:
            if args['align'] in ['left','center','right']:
                align = args['align']
        except:
            align = 'right'

        if align == 'left':
            graphtime += timespan
        elif align == 'center':
            graphtime += timespan/2
        if graphtime > int(time.time()):
            graphtime=int(time.time())
        graphtime =str(graphtime)

        graphTimeStart=str(timespan + timeoffset)
        graphTimeEnd=str(timeoffset)

        # scale the right y-axis according to the first scaled item if found, otherwise unscaled
        if int(graphWidth)>500:
            rightaxis = '--right-axis'
            scalestr = ' 1:0'
            for line in graph_lines:
                if line['name'] in lines and 'scale' in line:
                    scale = line['scale'].split(':')
                    try:
                        gain = float(scale[1])
                        offset = -float(scale[0])
                    except:
                        gain = 1
                        offset = 0
                    scalestr = " %s:%s"%(str(gain),str(offset))
                    break
            rightaxis += scalestr
        else:
            rightaxis = ''

        #Build the command string to make a graph from the database
        RrdGraphString1 =  "rrdtool graph - --disable-rrdtool-tag --border 0 "+ legends + bgcolor
        RrdGraphString1 += " --lower-limit 0 %s --full-size-mode --width %u"%(rightaxis, graphWidth) + " --right-axis-format %1.0lf "
        RrdGraphString1 += " --height %u --end %s-"%(graphHeight,graphtime) + graphTimeEnd + "s --start %s-"%graphtime + graphTimeStart + "s "
        RrdGraphString1 += "DEF:tickmark=%s:_logtick:AVERAGE TICK:tickmark#E7E7E7:1.0 "%db
        for line in graph_lines:
            if lines == '__all__' or line['name'] in lines:
                RrdGraphString1+="DEF:%s="%line['name']+db+":%s:AVERAGE "%line['ds_name']
                if 'scale' in line:
                    scale = line['scale'].split(':')
                    try:
                        gain = float(scale[1])
                        offset = float(scale[0])
                    except:
                        gain = 1
                        offset = 0
                    RrdGraphString1+="CDEF:%s_s=%s,%d,+,%d,/ "%(line['name'], line['name'], offset, gain)    
                    RrdGraphString1+="LINE1:%s_s%s:\"%s\" "% (line['name'], line['color'], line['name'])
                else:
                    RrdGraphString1+="LINE1:%s%s:\"%s\" "% (line['name'], line['color'], line['name'])
        cmd = subprocess.Popen(RrdGraphString1, shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def silolevel(self, **args):
        if not polling:
             return None
        try:
            reset_level=dbus.getItem('silo_reset_level')
            reset_time=dbus.getItem('silo_reset_time')
            reset_time = datetime.strptime(reset_time,'%d/%m/%y %H:%M')
            reset_time = mktime(reset_time.timetuple())
        except:
            return None
            
        try:
            maxWidth = args['maxWidth']
        except:
            maxWidth = '440'; # Default bootstrap 3 grid size
        if int(maxWidth)>500:
            rightaxis = '--right-axis 1:0'
        else:
            rightaxis = ''

        now=int(time.time())
        start=int(reset_time)
        RrdGraphString1=  "rrdtool graph - --border 0 --lower-limit 0 --disable-rrdtool-tag --full-size-mode --width %s %s --right-axis-format %%1.1lf --height 400 --end %u --start %u "%(maxWidth, rightaxis, now, start)   
        RrdGraphString1+=" DEF:a=%s:feeder_time:AVERAGE DEF:b=%s:feeder_capacity:AVERAGE"%(db,db)
        RrdGraphString1+=" CDEF:t=a,POP,TIME CDEF:tt=PREV\(t\) CDEF:i=t,tt,-"
        #RrdGraphString1+=" CDEF:a1=t,%u,GT,tt,%u,LE,%s,0,IF,0,IF"%(start,start,reset_level)
        #RrdGraphString1+=" CDEF:a2=t,%u,GT,tt,%u,LE,3000,0,IF,0,IF"%(start+864000*7,start+864000*7)
        #RrdGraphString1+=" CDEF:s1=t,%u,GT,tt,%u,LE,%s,0,IF,0,IF"%(start, start, reset_level)
        RrdGraphString1+=" CDEF:s1=t,POP,COUNT,1,EQ,%s,0,IF"%reset_level
        RrdGraphString1+=" CDEF:s=a,b,*,360000,/,i,*" 
        RrdGraphString1+=" CDEF:fs=s,UN,0,s,IF" 
        RrdGraphString1+=" CDEF:c=s1,0,EQ,PREV,UN,0,PREV,IF,fs,-,s1,IF AREA:c#d6e4e9"
        cmd = subprocess.Popen(RrdGraphString1, shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def consumption(self, **args):
        if not polling:
             return None
        if consumption_graph:
            try:
                maxWidth = args['maxWidth']
            except:
                maxWidth = '440'; # Default bootstrap 3 grid size
            if int(maxWidth)>500:
                rightaxis = '--right-axis 1:0'
            else:
                rightaxis = ''
            now = int(time.time())
            align = now/3600*3600
            RrdGraphString = make_barchart_string(db, now, align, 3600, 24, '-', maxWidth, '24h consumption', 'kg/h', param=rightaxis)
            cmd = subprocess.Popen(RrdGraphString, shell=True, stdout=subprocess.PIPE)
            cherrypy.response.headers['Pragma'] = 'no-cache'
            cherrypy.response.headers['Content-Type'] = "image/png"
            return cmd.communicate()[0]

    @cherrypy.expose
    @require() #requires valid login
    def getparam(self, param='-'):
        parameterlist=dbus.getdb()
        if cherrypy.request.method == "GET":
            if param in(parameterlist):
                try:
                    result = dbus.getItem(param)
                except:
                    result = 'error'
            else: result = 'not found'
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(dict(param=param, value=result))

    @cherrypy.expose
    @require() #requires valid login
    def setparam(self, param='-', data=None):
        parameterlist=dbus.getdb()
        if cherrypy.request.method == "POST":
            if param in(parameterlist):
                try:
                    result = dbus.setItem(param, data)
                except:
                    result = 'error'
            else: result = 'not found'
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(dict(param=param, value=result))

    @cherrypy.expose
    @require() #requires valid login
    def parameters(self, t1='', t2='', t3='', t4='', **args):
        # Get list of data/parameters
        try:
            level=cherrypy.session['level']
        except:
            cherrypy.session['level'] = 'Basic'
        level=cherrypy.session['level']
        try:
            parameterlist = dbus.getFullDB([level,t1,t2,t3,t4])
            # Set up a queue and start a thread to read all items to the queue, the parameter view will empty the queue bye calling /getparams/
            paramQueue = Queue.Queue(300)
            # Store the queue in the session
            cherrypy.session['paramReaderQueue'] = paramQueue
            ht = threading.Thread(target=parameterReader, args=(paramQueue,parameterlist))
            ht.start()
            values=['']*len(parameterlist)
            params={}
            paramlist=[]
            datalist=[]
            commandlist=[]
            for item in parameterlist:
                if item['type'] == 'R':
                    datalist.append(item)
                if item['type'] == 'R/W':
                    paramlist.append(item)
                if item['type'] == 'W':
                    commandlist.append(item)
                try:
                    a = item['longname']
                except:
                    item['longname'] = item['name']
                try:
                    a = item['unit']
                except:
                    item['unit'] = ''
                try:
                    a = item['description']
                except:
                    item['description'] = ''

                params[item['name']] = ' '
                if args.has_key(item['name']):
                    if cherrypy.request.method == "POST":
                        # set parameter
                        try:
                            values[parameterlist.index(item['name'])]=dbus.setItem(item['name'], args[item['name']][1])
                        except:
                            values[parameterlist.index(item['name'])]='error'
                    else:
                        # get parameter
                        try:
                            values[parameterlist.index(item['name'])]=escape(dbus.getItem(item['name']))
                        except:
                            values[parameterlist.index(item['name'])]='error'
            tmpl = lookup.get_template("parameters.html")
            tags = dbus.getMenutags()
            return tmpl.render(username=cherrypy.session.get('_cp_username'), data = datalist, params=paramlist, commands=commandlist, values=values, level=level, heading=t1, tags=tags)
        except DbusNotConnected:
            return "Pellmonsrv not running?"

    # Empty the item/value queue, call several times until all data is retrieved
    @cherrypy.expose
    @require() #requires valid login
    def getparams(self):
        parameterlist=dbus.getdb()
        paramReaderQueue = cherrypy.session.get('paramReaderQueue')
        params={}
        if paramReaderQueue:
            while True:
                try:
                    param,value = paramReaderQueue.get_nowait()
                    if param=='**end**':
                        # remove the queue when all items read
                        del cherrypy.session['paramReaderQueue']
                        break
                    params[param]=value
                except:
                    # queue is empty, send what's read so far
                    break
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(params)

    @cherrypy.expose
    @require() #requires valid login
    def setlevel(self, level='Basic'):
        cherrypy.session['level']=level
        # redirect back after setting selection in session
        raise cherrypy.HTTPRedirect(cherrypy.request.headers['Referer'])

    @cherrypy.expose
    def index(self, **args):
        autorefresh = cherrypy.session.get('autorefresh')=='yes'
        empty=True
        for key, val in polldata:
            if colorsDict.has_key(key):
                if cherrypy.session.get(val)=='yes':
                    empty=False
        tmpl = lookup.get_template("index.html")
        try:
            lines = cherrypy.session['lines']
        except:
            lines = ','.join([line['name'] for line in graph_lines])
            cherrypy.session['lines'] = lines
        try:
            timespan = cherrypy.session['timespan']
        except:
            timespan = 3600
            cherrypy.session['timespan'] = timespan
        timeName = 'sdfas'
        for i in range(len(timeNames)):
            if timeSeconds[i] == timespan:
                timeName = timeNames[i]
                break;
        return tmpl.render(username=cherrypy.session.get('_cp_username'), empty=False, autorefresh=autorefresh, timeSeconds = timeSeconds, timeChoices=timeChoices, timeNames=timeNames, timeChoice=timespan, graphlines=graph_lines, selectedlines = lines, timeName = timeName)

class WsHandler:
    @cherrypy.expose
    def ws(self, parameters='', events='no'):
        db=dbus.getdb()
        parameters = parameters.split(',')
        params = [param for param in parameters if param in(db)]
        sensor = Sensor(params, cherrypy.request.ws_handler, events == 'yes')

def parameterReader(q, parameterlist):
    #parameterlist=dbus.getdb()
    for item in parameterlist:
        try:
            value = escape(dbus.getItem(item['name']))
        except:
            value='error'
        q.put((item['name'],value))
    q.put(('**end**','**end**'))


HERE = os.path.dirname(webpath)
MEDIA_DIR = os.path.join(HERE, 'media')
FAVICON = os.path.join(MEDIA_DIR, 'favicon.ico')

#Look for temlates in this directory
lookup = TemplateLookup(directories=[os.path.join(HERE, 'html')])

parser = ConfigParser.ConfigParser()
config_file = 'pellmon.conf'

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(prog='pellmonweb')
    argparser.add_argument('-D', '--DAEMONIZE', action='store_true', help='Run as daemon')
    argparser.add_argument('-P', '--PIDFILE', default='/tmp/pellmonweb.pid', help='Full path to pidfile')
    argparser.add_argument('-U', '--USER', help='Run as USER')
    argparser.add_argument('-G', '--GROUP', default='nogroup', help='Run as GROUP')
    argparser.add_argument('-C', '--CONFIG', default='pellmon.conf', help='Full path to config file')
    argparser.add_argument('-d', '--DBUS', default='SESSION', choices=['SESSION', 'SYSTEM'], help='which bus to use, SESSION is default')
    args = argparser.parse_args()

    dbus = Dbus_handler(args.DBUS)

    config_file = args.CONFIG

    pidfile = args.PIDFILE
    if pidfile:
        plugins.PIDFile(cherrypy.engine, pidfile).subscribe()

    if args.USER:
        # Load the configuration file
        if not os.path.isfile(config_file):
            config_file = '/etc/pellmon.conf'
        if not os.path.isfile(config_file):
            config_file = '/usr/local/etc/pellmon.conf'
        if not os.path.isfile(config_file):
            print "config file not found"
            sys.exit(1)
        parser.read(config_file)

        try:
            accesslog = parser.get('weblog', 'accesslog')
            logdir = os.path.dirname(accesslog)
            if not os.path.isdir(logdir):
                os.mkdir(logdir)
            uid = pwd.getpwnam(args.USER).pw_uid
            gid = grp.getgrnam(args.GROUP).gr_gid
            os.chown(logdir, uid, gid)
            if os.path.isfile(accesslog):
                os.chown(accesslog, uid, gid)
        except:
            pass
        try:
            errorlog = parser.get('weblog', 'errorlog')
            logdir = os.path.dirname(errorlog)
            if not os.path.isdir(logdir):
                os.mkdir(logdir)
            uid = pwd.getpwnam(args.USER).pw_uid
            gid = grp.getgrnam(args.GROUP).gr_gid
            os.chown(logdir, uid, gid)
            if os.path.isfile(errorlog):
                os.chown(errorlog, uid, gid)
        except:
            pass
        uid = pwd.getpwnam(args.USER).pw_uid
        gid = grp.getgrnam(args.GROUP).gr_gid
        plugins.DropPrivileges(cherrypy.engine, uid=uid, gid=gid, umask=033).subscribe()

    # Load the configuration file
    if not os.path.isfile(config_file):
        config_file = '/etc/pellmon.conf'
    if not os.path.isfile(config_file):
        config_file = '/usr/local/etc/pellmon.conf'
    if not os.path.isfile(config_file):
        print "config file not found"
        sys.exit(1)
    parser.read(config_file)

    # The RRD database, updated by pellMon
    try:
        polling = True
        db = parser.get('conf', 'database')
        graph_file = os.path.join(os.path.dirname(db), 'graph.png')
    except ConfigParser.NoOptionError:
        polling = False
        db = ''

    # the colors to use when drawing the graph
    try:
        colors = parser.items('graphcolors')
        colorsDict = {}
        for key, value in colors:
            colorsDict[key] = value
    except ConfigParser.NoSectionError:
        colorsDict = {}

    # Get the names of the polled data
    polldata = parser.items("pollvalues")

    try:
        # Get the names of the polled data
        rrd_ds_names = parser.items("rrd_ds_names")
        ds_names = {}
        for key, value in rrd_ds_names:
            ds_names[key] = value
    except ConfigParser.NoSectionError:
        ds_names = {}

    try:
        # Get the optional scales
        scales = parser.items("scaling")
        scale_data = {}
        for key, value in scales:
            scale_data[key] = value
    except ConfigParser.NoSectionError:
        scale_data = {}

    graph_lines=[]
    for key,value in polldata:
        if key in colorsDict and key in ds_names:
            graph_lines.append({'name':value, 'color':colorsDict[key], 'ds_name':ds_names[key]})
            if key in scale_data:
                graph_lines[-1]['scale'] = scale_data[key]

    credentials = parser.items('authentication')
    logfile = parser.get('conf', 'logfile')

    timeChoices = ['time1h', 'time3h', 'time8h', 'time24h', 'time3d', 'time1w']
    timeNames  = ['1 hour', '3 hours', '8 hours', '24 hours', '3 days', '1 week']
    timeSeconds = [3600, 3600*3, 3600*8, 3600*24, 3600*24*3, 3600*24*7]
    ft=False
    fc=False
    for a,b in polldata:
        if b=='feeder_capacity':
            fc=True
        if b=='feeder_time':
            ft=True
    if fc and ft:
        consumption_graph=True
        consumption_file = os.path.join(os.path.dirname(db), 'consumption.png')
    else:
        consumption_graph=False
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()
    global_conf = {
            'global':   { #w'server.environment': 'debug',
                          'tools.sessions.on' : True,
                          'tools.sessions.timeout': 7200,
                          'tools.auth.on': True,
                          'server.socket_host': '0.0.0.0',
                          'server.socket_port': int(parser.get('conf', 'port')),

                          #'engine.autoreload.on': False,
                          #'checker.on': False,
                          #'tools.log_headers.on': False,
                          #'request.show_tracebacks': False,
                          'request.show_mismatched_params': False,
                          #'log.screen': False,
                          'engine.SIGHUP': None,
                          'engine.SIGTERM': None,

                        }
                  }
    app_conf =  {'/media':
                    {'tools.staticdir.on': True,
                     'tools.staticdir.dir': MEDIA_DIR},
                 '/favicon.ico':
                    {'tools.staticfile.on':True,
                     'tools.staticfile.filename': FAVICON},
                }

    if websockets:
        ws_conf = {'/ws':
                     {'tools.websocket.on': True,
                      'tools.websocket.handler_cls': WebSocket}
                  }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update(global_conf)

    # Only daemonize if asked to.
    if args.DAEMONIZE:
        # Don't print anything to stdout/sterr.
        cherrypy.config.update({'log.screen': False, 'engine.autoreload.on': False})
        plugins.Daemonizer(cherrypy.engine).subscribe()

    cherrypy.tree.mount(PellMonWeb(), '/', config=app_conf)
    if websockets:
        cherrypy.tree.mount(WsHandler(), '/websocket', config=ws_conf)

    try:
        cherrypy.config.update({'log.access_file':accesslog})
    except:
        pass
    try:
        cherrypy.config.update({'log.error_file':errorlog})
    except:
        pass

    GObject.threads_init()

    # Always start the engine; this will start all other services
    try:
        cherrypy.engine.start()
    except:
        # Assume the error has been logged already via bus.log.
        sys.exit(1)
    else:
        # Needed to be able to use threads with a glib main loop running

        # A main loop is needed for dbus "name watching" to work
        main_loop = GLib.MainLoop()

        # cherrypy has it's own mainloop, cherrypy.engine.block, that
        # regularly calls engine.publish every 100ms. The most reliable
        # way to run dbus and cherrypy together seems to be to use the
        # glib mainloop for both, ie call engine.publish from the glib 
        # mainloop instead of calling engine.block.
        def publish():
            try:
                cherrypy.engine.publish('main')
                if cherrypy.engine.execv:
                    main_loop.quit()
                    cherrypy.engine._do_execv()
            except KeyboardInterrupt:
                pass
            return True

        # Use our own signal handler to stop on ctrl-c, seems to be simpler
        # than subscribing to cherrypy's signal handler
        def signal_handler(signal, frame):
            cherrypy.engine.exit()
            main_loop.quit()
        signal.signal(signal.SIGINT, signal_handler)

        # Handle cherrypy's main loop needs from here
        GLib.timeout_add(100, publish)

        dbus.start()
        try:
            main_loop.run()
        except KeyboardInterrupt:
            pass


