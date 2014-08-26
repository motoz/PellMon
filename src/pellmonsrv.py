#! /usr/bin/python
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

import signal, os, Queue, threading, glib
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import logging
import logging.handlers
import sys
import ConfigParser
import time
from smtplib import SMTP 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import argparse
import pwd, grp
from Pellmonsrv.yapsy.PluginManager import PluginManager
from Pellmonsrv.plugin_categories import protocols
from Pellmonsrv import Daemon
import subprocess
import sys, traceback
import urllib2 as urllib
from Pellmonsrv import __file__ as pluginpath

def dbus_msg_to_string(msg):
    ls = []
    for d in msg:
        ls.append(d['name'] + ':' + d['value'])
    return ';'.join(ls)

class dbus_signal_handler(logging.Handler):
    """Emit log messages as a dbus signal"""
    def __init__(self, dbus_service):
        logging.Handler.__init__(self)
        self.dbus_service = dbus_service
    def emit(self, record):
        msg = self.format(record)
        #self.dbus_service.changed_parameters([{'name':'__event__', 'value':msg}])
        s = dbus_msg_to_string([{'name':'__event__', 'value':msg}])
        self.dbus_service.changed_parameters(s)

class Database(threading.Thread):
    def __init__(self):
        class getset:
            def __init__(self, item, obj):
                self.item = item
                self.obj = obj
            def getItem(self):
                return self.obj.getItem(self.item)
            def setItem(self, value):
                return self.obj.setItem(self.item, value)
        threading.Thread.__init__(self)
        self.dbus_service = None
        self.items={}
        self.values={}
        self.protocols=[]
        self.setDaemon(True)
        # Initialize and activate all plugins of 'Protocols' category
        global manager
        manager = PluginManager(categories_filter={ "Protocols": protocols})
        manager.setPluginPlaces([conf.plugin_dir])
        manager.collectPlugins()
        for plugin in manager.getPluginsOfCategory('Protocols'):
            if plugin.name in conf.enabled_plugins:
                try:
                    plugin.plugin_object.activate(conf.plugin_conf[plugin.name], globals())
                    self.protocols.append(plugin)
                    logger.info("activated plugin %s"%plugin.name)
                    for item in plugin.plugin_object.getDataBase():
                        self.items[item] = getset(item, plugin.plugin_object)
                except Exception as e:
                    logger.info('Plugin %s init failed'%plugin.name)
                    logger.debug('Plugin error:%s'%(traceback.format_exc(sys.exc_info()[1])))
        self.start()

    def run(self):
        while True:
            time.sleep(2)
            changed_params = []
            for item_name in self.items:
                try:
                    value = self.items[item_name].getItem()
                    if item_name in self.values:
                        if value != self.values[item_name]:
                            changed_params.append({'name':item_name, 'value':value})
                            self.values[item_name] = value
                    else:
                        changed_params.append({'name':item_name, 'value':value})
                        self.values[item_name] = value
                except:
                    pass
            if changed_params:
                if self.dbus_service:
                    s = dbus_msg_to_string(changed_params)
                    #self.dbus_service.changed_parameters(changed_params)
                    self.dbus_service.changed_parameters(s)

    def terminate(self):
        for p in self.protocols:
            p.plugin_object.deactivate()
            logger.info('deactivated %s'%p.name)

class MyDBUSService(dbus.service.Object):
    """Publish an interface over the DBUS system bus"""
    def __init__(self, bus='SESSION'):
        if bus=='SESSION':
            bus=dbus.SessionBus()
        else:
            bus=dbus.SystemBus()
        bus_name = dbus.service.BusName('org.pellmon.int', bus)
        dbus.service.Object.__init__(self, bus_name, '/org/pellmon/int')

    @dbus.service.method('org.pellmon.int')
    def GetItem(self, param):
        """Get the value for a data/parameter item"""
        if param == 'pellmonsrv_version':
            return '0.0.0'
        else:
            return conf.database.items[param].getItem()

    @dbus.service.method('org.pellmon.int')
    def SetItem(self, param, value):
        """Get the value for a parameter/command item"""
        return conf.database.items[param].setItem(value)

    @dbus.service.method('org.pellmon.int')
    def GetDB(self):
        """Get list of all data/parameter/command items"""
        db=[]
        for plugin in conf.database.protocols:
            db = db + plugin.plugin_object.getDataBase()
        db.sort()
        return db

    @dbus.service.method(dbus_interface='org.pellmon.int', in_signature='as', out_signature='aa{sv}')
    def GetFullDB(self, tags):
        """Get list of all data/parameter/command items"""
        db=[]
        for plugin in conf.database.protocols:
            db = db + plugin.plugin_object.GetFullDB(tags)
        return db

    @dbus.service.method('org.pellmon.int')
    def getMenutags(self):
        """Get list of all tags that make up the menu"""
        menutags=[]
        for plugin in conf.database.protocols:
            menutags = menutags + plugin.plugin_object.getMenutags()
        return menutags

    #@dbus.service.signal(dbus_interface='org.pellmon.int', signature='aa{sv}')
    @dbus.service.signal(dbus_interface='org.pellmon.int', signature='s')
    def changed_parameters(self, message):
        pass

def pollThread():
    """Poll data defined in conf.pollData and update the RRD database with the responses"""
    logger.debug('handlerTread started by signal handler')
    itemlist=[]
    global conf
    if not conf.polling:
        return
    try:
        for data in conf.pollData:
            # 'special cases' handled here, name starting with underscore are not polled from the protocol 
            if data['name'][0] == '_':
                if data['name'] == '_logtick':
                    itemlist.append(str(conf.tickcounter))
                else:
                    itemlist.append('U')
            else:
                try:
                    value = conf.database.items[data['name']].getItem()
                except KeyError:
                    # write 'undefined' to noexistent data points
                    value = 'U'
                # when a counter is updated with a smaller value than the previous one, rrd thinks the counter has wrapped
                # either at 32 or 64 bits, which leads to a huge spike in the counter if it really didn't
                # To prevent this we write an undefined value before an update that is less than the previous
                if 'COUNTER' in data['ds_type']:
                    try:
                        if int(value) < int(conf.lastupdate[data['name']]):
                            value = 'U'
                    except:
                        pass
                itemlist.append(value)
                conf.lastupdate[data['name']] = value
        s=':'.join(itemlist)
        os.system("/usr/bin/rrdtool update "+conf.db+" %u:"%(int(time.time())/10*10)+s)
    except IOError as e:
        logger.debug('IOError: '+e.strerror)
        logger.debug('   Trying Z01...')
        try:
            # I have no idea why, but every now and then the pelletburner stops answering, and this somehow causes it to start responding normally again
            conf.database.items['oxygen_regulation'].getItem()
        except IOError as e:
            logger.info('Getitem failed two times and reading Z01 also failed '+e.strerror)

def handle_settings_changed(item, oldvalue, newvalue, itemtype):
    """ Called by the protocols when they detect that a setting has changed """
    if itemtype == 'parameter':
        logline = """Parameter '%s' changed from '%s' to '%s'"""%(item, oldvalue, newvalue)
        logger.info(logline)
        conf.tickcounter=int(time.time())
        if conf.email and 'parameter' in conf.emailconditions:
            sendmail(logline)
    if itemtype == 'mode':
        logline = """'%s' changed from '%s' to '%s'"""%(item, oldvalue, newvalue)
        logger.info(logline)
        conf.tickcounter=int(time.time())
        if conf.email and 'mode' in conf.emailconditions:
            sendmail(logline)
    if itemtype == 'alarm':
        logline = """'%s' state went from '%s' to '%s'"""%(item, oldvalue, newvalue)
        logger.info(logline)
        conf.tickcounter=int(time.time())
        if conf.email and 'alarm' in conf.emailconditions:
            sendmail(logline)

def periodic_signal_handler(signum, frame):
    """Periodic signal handler. Start pollThread to do the work"""
    ht = threading.Thread(name='pollThread', target=pollThread)
    ht.setDaemon(True)
    ht.start()

def copy_db(direction='store'):
    """Copy db to nvdb or nvdb to db depending on direction"""
    global copy_in_progress
    if not 'copy_in_progress' in globals():
        copy_in_progress = False        
    if not copy_in_progress:
        if direction=='store':
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(conf.db, conf.nvdb)) 
                logger.debug('copied %s to %s'%(conf.db, conf.nvdb))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(conf.db, conf.nvdb))
            finally:
                copy_in_progress = False
        else:
            try:
                copy_in_progress = True     
                os.system('cp %s %s'%(conf.nvdb, conf.db))  
                logger.info('copied %s to %s'%(conf.nvdb, conf.db))
            except Exception, e:
                logger.info(str(e))
                logger.info('copy %s to %s failed'%(conf.nvdb, conf.db))
            finally:
                copy_in_progress = False
    
def db_copy_thread():
    """Run periodically at db_store_interval to call copy_db""" 
    try:
        copy_db('store')    
    except:
        pass
    ht = threading.Timer(conf.db_store_interval, db_copy_thread)
    ht.setDaemon(True)
    ht.start()

def sigterm_handler(signum, frame):
    """Handles SIGTERM, waits for the database copy on shutdown if it is in a ramdisk"""
    logger.info('stop')
    conf.database.terminate()
    if conf.polling: 
        if conf.nvdb != conf.db:   
            copy_db('store')
        if not copy_in_progress:
            logger.info('exiting')
            sys.exit(0)
    else:
        logger.info('exiting')
        sys.exit(0)
    

def sendmail(msg, wait=2, followup=True):
    ht = threading.Timer(wait, sendmail_thread, args=(msg, followup))
    ht.start()

def sendmail_thread(msg, followup):
    try:
        username = conf.emailusername 
        password = conf.emailpassword

        # Create message container.
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = conf.emailsubject
        msgRoot['From'] = conf.emailfromaddress
        msgRoot['To'] = conf.emailtoaddress

        if conf.email_graph and conf.port:
            graphlines = '&lines='+conf.email_graphlines if conf.email_graphlines else ''
            if conf.email_followup and not followup:
                align = 'center'
                timespan = conf.email_followup*2
            else:
                align = 'right'
                timespan = conf.email_timespan
                
            fd = urllib.urlopen("http://localhost:%s%s+/graph?width=%u&height=%u&timespan=%u&legends=yes&bgcolor=ffffff%s&align=%s"%(conf.port, conf.webroot, conf.email_width, conf.email_height, timespan, graphlines, align))
            img = fd.read()

            msgImg = MIMEImage(img, 'png')
            msgImg.add_header('Content-ID', '<image1>')
            msgImg.add_header('Content-Disposition', 'inline', filename='graph.png')
            imagehtml = '<img src="cid:image1">'
        else:
            imagehtml = ''
            msgImg = None

        if conf.email_mode == 'html':
            # Create the body of the message.
            html = """\
            <p>%s<br/>
            %s
            </p>
            """%(msg,imagehtml)
            message = MIMEText(html, 'html')
        else:
            message = MIMEText(msg)
        msgRoot.attach(message)
        if msgImg:
            msgRoot.attach(msgImg)

        mailserver = SMTP(conf.emailserver)
        mailserver.starttls() 
        mailserver.login(conf.emailusername, conf.emailpassword)
        mailserver.sendmail(msgRoot['From'], msgRoot['To'], msgRoot.as_string())
        mailserver.quit()
        logger.info('status email sent')
    except Exception, e:
        logger.info('error trying to send email')
        logger.info(str(e))
    if followup and conf.email_followup:
        sendmail('Pellmon status followup', conf.email_followup, False)

class MyDaemon(Daemon):
    """ Run after double fork with start, or directly with debug argument"""
    def run(self):
        global logger
        logger = logging.getLogger('pellMon')
        logger.info('starting pelletMonitor')

        # Load all plugins of 'protocol' category.
        conf.database = Database()

        try:
            if conf.USER:
                drop_privileges(conf.USER, conf.GROUP)
        except:
            pass

        # DBUS needs the gobject main loop, this way it seems to work...
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()    
        DBUSMAINLOOP = gobject.MainLoop()
        DBusGMainLoop(set_as_default=True)
        conf.myservice = MyDBUSService(conf.dbus)
        conf.database.dbus_service = conf.myservice
        
        # Add a handler that signals log messages over dbus
        dh = dbus_signal_handler(conf.myservice)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        dh.setFormatter(formatter)
        logger.addHandler(dh)

        # Create RRD database if does not exist
        if conf.polling:
            if not os.path.exists(conf.nvdb):
                os.system(conf.RrdCreateString)
                logger.info('Created rrd database: '+conf.RrdCreateString)

            # If nvdb is different from db, copy nvdb to db
            if conf.nvdb != conf.db:
                copy_db('restore')
                # Create and start db_copy_thread to store db at regular interval
                ht = threading.Timer(conf.db_store_interval, db_copy_thread)
                ht.setDaemon(True)
                ht.start()

            # Get the latest values for all data sources in the database
            s = subprocess.check_output(['rrdtool', 'lastupdate', conf.db])
            l=s.split('\n')
            items = l[0].split()
            values = l[2].split()
            values = values[1::]
            conf.lastupdate = dict(zip(items, values))

        # Create SIGTERM signal handler
        signal.signal(signal.SIGTERM, sigterm_handler)

        # Create poll_interval periodic signal handler
        signal.signal(signal.SIGALRM, periodic_signal_handler)
        logger.debug('created signalhandler')
        signal.setitimer(signal.ITIMER_REAL, 2, conf.poll_interval)
        logger.debug('started timer')
        # Execute glib main loop to serve DBUS connections
        DBUSMAINLOOP.run()

        # glib main loop has quit, this should not happen
        logger.info("ending, what??")
        
class config:
    """Contains global configuration, parsed from the .conf file"""
    def __init__(self, filename):
        # Load the configuration file
        parser = ConfigParser.ConfigParser()
        parser.optionxform=str
        parser.read(filename)

        # Get the enabled plugins list
        plugins = parser.items("enabled_plugins")
        self.enabled_plugins = []
        self.plugin_conf={}
        for key, plugin_name in plugins:
            self.enabled_plugins.append(plugin_name)
            self.plugin_conf[plugin_name] = {}
            try:
                plugin_conf = parser.items('plugin_%s'%plugin_name)
                for key, value in plugin_conf:
                    self.plugin_conf[plugin_name][key] = value
            except:
                # No plugin config found
                pass

        # Data to write to the rrd
        polldata = parser.items("pollvalues")

        # rrd database datasource names
        rrd_ds_names = parser.items("rrd_ds_names")

        # Optional rrd data type definitions
        rrd_ds_types = parser.items("rrd_ds_types")

        # Make a list of data to poll, in the order they appear in the rrd database
        self.pollData = []
        ds_types = {}
        pollItems = {}
        for key, value in polldata:
            pollItems[key] = value
        for key, value in rrd_ds_names:
            ds_types[key] = "DS:%s:GAUGE:%u:U:U"
        for key, value in rrd_ds_types:
            ds_types[key] = value
        for key, value in rrd_ds_names:
            self.pollData.append({'key':key, 'name':pollItems[key], 'ds_name':value, 'ds_type':ds_types[key]})

        # The RRD database
        try:
            self.polling=True
            self.db = parser.get('conf', 'database')
        except ConfigParser.NoOptionError:
            self.polling=False

        # The persistent RRD database
        try:
            self.nvdb = parser.get('conf', 'persistent_db') 
        except ConfigParser.NoOptionError:
            if self.polling:
                self.nvdb = self.db        
        try:
            self.db_store_interval = int(parser.get('conf', 'db_store_interval'))
        except ConfigParser.NoOptionError:
            self.db_store_interval = 3600

        # create logger
        global logger
        logger = logging.getLogger('pellMon')
        loglevel = parser.get('conf', 'loglevel')
        loglevels = {'info':logging.INFO, 'debug':logging.DEBUG}
        try:
            logger.setLevel(loglevels[loglevel])
        except:
            logger.setLevel(logging.DEBUG)
        # create file handler for logger
        fh = logging.handlers.WatchedFileHandler(parser.get('conf', 'logfile'))
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)

        try: 
            self.poll_interval = int(parser.get('conf', 'pollinterval'))
        except ConfigParser.NoOptionError:
            logger.info('Invalid poll_interval setting, using 10s')
            self.poll_interval = 10

        if self.polling:
            # Build a command string to create the rrd database
            self.RrdCreateString="rrdtool create %s --step %u "%(self.nvdb, self.poll_interval)
            for item in self.pollData:
                self.RrdCreateString += item['ds_type'] % (item['ds_name'], self.poll_interval*4) + ' ' 
            self.RrdCreateString += "RRA:AVERAGE:0,999:1:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:10:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:100:20000 " 
            self.RrdCreateString += "RRA:AVERAGE:0,999:1000:20000" 

        # dict to hold known recent values of db items
        self.dbvalues = {} 

        # count every parameter and mode change so rrd can draw a tick mark when that happens
        self.tickcounter = int(time.time())
        
        try:
            self.emailusername = parser.get('email', 'username')
            self.emailpassword = parser.get('email', 'password')
            self.emailfromaddress = parser.get('email', 'from')
            self.emailtoaddress = parser.get('email', 'to')
            self.emailsubject = parser.get('email', 'subject')
            self.emailserver = parser.get('email', 'server')
            self.emailconditions = parser.get('email', 'conditions')
            self.email=True
        except ConfigParser.NoOptionError:
            self.email=False
        try:
            self.port = parser.get('conf', 'port')
        except:
            self.port = None
        try:
            self.webroot = parser.get('conf', 'webroot')
        except:
            self.webroot = ""
        if self.webroot[-1:] == '/':
            self.webroot = self.webroot[:-1]
        if len(self.webroot)>=1 and self.webroot[0] != '/':
            self.webroot='/'+self.webroot
        try:
            self.email_mode = parser.get('email', 'mode')
        except:
            self.email_mode = 'text'
        try:
            graphsize = parser.get('email', 'graphsize')
            self.email_width = int(graphsize.split('x')[0])
            self.email_height = int(graphsize.split('x')[1])
            self.email_graph = True
        except:
            self.email_graph = False
        try:
            self.email_timespan = int(parser.get('email', 'graphtimespan'))
        except:
            self.email_timespan = 3600
        try:
            graphlines = parser.get('email', 'graphlines').split(',')
            self.email_graphlines = ','.join([line['name'] for line in self.pollData if line['key'] in graphlines])
        except:
            self.email_graphlines = None
        try:
            self.email_followup = int(parser.get('email', 'followup'))
        except:
            self.email_followup = None


def getgroups(user):
    gids = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    gids.append(grp.getgrgid(gid).gr_gid)
    return gids
    
def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so don't do anything
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    #Set the new uid/gid
    os.setgid(running_gid)
    try:
        # Set supplementary group privileges
        gids = getgroups(uid_name)
        os.setgroups(gids)
    except:
        # Can live without it for testing purposes
        pass
    os.setuid(running_uid)

    # Set umask
    old_umask = os.umask(033)


#########################################################################################



if __name__ == "__main__":

    daemon = MyDaemon()
    commands = {
        'start':daemon.start,
        'stop':daemon.stop,
        'restart':daemon.restart,
        'debug':daemon.run}

    parser = argparse.ArgumentParser(prog='pellmonsrv')
    parser.add_argument('command', choices=commands, help="With debug argument pellmonsrv won't daemonize")
    parser.add_argument('-P', '--PIDFILE', default='/tmp/pellmonsrv.pid', help='Full path to pidfile')
    parser.add_argument('-U', '--USER', help='Run as USER')
    parser.add_argument('-G', '--GROUP', default='nogroup', help='Run as GROUP')
    parser.add_argument('-C', '--CONFIG', default='pellmon.conf', help='Full path to config file')
    parser.add_argument('-D', '--DBUS', default='SESSION', choices=['SESSION', 'SYSTEM'], help='which bus to use, SESSION is default')
    parser.add_argument('-p', '--PLUGINDIR', default='-', help='Full path to plugin directory')
    args = parser.parse_args()
    if args.PLUGINDIR == '-':
        args.PLUGINDIR = os.path.join(os.path.dirname(pluginpath), 'plugins')

    config_file = args.CONFIG
    if not os.path.isfile(config_file):
        config_file = '/etc/pellmon.conf'
    if not os.path.isfile(config_file):
        config_file = '/usr/local/etc/pellmon.conf'
    if not os.path.isfile(config_file):
        sys.exit(1)

    if args.USER:
        parser = ConfigParser.ConfigParser()
        parser.read(config_file)

        logfile = parser.get('conf', 'logfile')
        logdir = os.path.dirname(logfile)
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
        uid = pwd.getpwnam(args.USER).pw_uid
        gid = grp.getgrnam(args.GROUP).gr_gid
        os.chown(logdir, uid, gid)
        if os.path.isfile(logfile):
            os.chown(logfile, uid, gid)

        dbfile = parser.get('conf', 'database')
        dbdir = os.path.dirname(dbfile)
        if not os.path.isdir(dbdir):
            os.mkdir(dbdir)
        uid = pwd.getpwnam(args.USER).pw_uid
        gid = grp.getgrnam(args.GROUP).gr_gid
        os.chown(dbdir, uid, gid)
        if os.path.isfile(dbfile):
            os.chown(dbfile, uid, gid)

    # must be be set before calling daemon.start
    daemon.pidfile = args.PIDFILE

    # Init global configuration from the conf file
    global conf
    conf = config(config_file)
    conf.dbus = args.DBUS
    conf.plugin_dir = args.PLUGINDIR

    if args.USER:
        conf.USER = args.USER
    if args.GROUP:
        conf.GROUP = args.GROUP


    commands[args.command]()

