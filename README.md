PellMon
=======

PellMon is logging, monitoring and configuration daemon for pellet burners. It uses plugins to communicate
with a pellet burner. Two plugins are included, ScotteCom and RaspberryGPIO. ScotteCom uses a serial
interface to communicate with a NBE scotte/woody/biocomfort V4, V5 or V6 pellet burner. It provides access to 
most configuration parameters and measurement data. The RaspberryGPIO plugin uses the hardware gpio on a raspberry pi 
single board computer to count feeder auger revolutions and calculates burner power and pellet consumption. The plugin 
system makes it easy to add custom plugins for extended functionality. 

PellMon is also a webserver and a webapplication. It serves a responsive mobile friendly webapp with a graph of
selected measurement values, bar charts with calculated pellet consumption, event log and parameter settings. 

PellMon also has a command line interface to access all data provided by the plugins, for easy integration in other
systems. 

####Contains:

###pellmonsrv.py:
Communication daemon. Implements a DBUS interface for reading and writing setting values and reading of measurement data. Optionally handles logging of measurement data to an RRD database. 
<pre>
usage: pellmonsrv.py [-h] [-P PIDFILE] [-U USER] [-G GROUP] [-C CONFIG] [-D {SESSION,SYSTEM}] [-p PLUGINDIR]
                  {debug,start,stop,restart}

positional arguments:
  {debug,start,stop,restart}
                        With debug argument pellmonsrv won't daemonize

optional arguments:
  -h, --help            show this help message and exit
  -P PIDFILE, --PIDFILE PIDFILE
                        Full path to pidfile
  -U USER, --USER USER  Run as USER
  -G GROUP, --GROUP GROUP
                        Run as GROUP
  -C CONFIG, --CONFIG CONFIG
                        Full path to config file
  -D {SESSION,SYSTEM}, --DBUS {SESSION,SYSTEM}
                        which bus to use, SESSION is default
  -p PLUGINDIR, --PLUGINDIR PLUGINDIR
                        Full path to plugin directory
</pre>

###pellmonweb.py:
Webserver and webapp, plotting of measurement, calculated consumption and data and parameter reading/writing.
<pre>
usage: pellmonweb.py [-h] [-D] [-P PIDFILE] [-U USER] [-G GROUP] [-C CONFIG] [-d {SESSION,SYSTEM}]

optional arguments:
  -h, --help            show this help message and exit
  -D, --DAEMONIZE       Run as daemon
  -P PIDFILE, --PIDFILE PIDFILE
                        Full path to pidfile
  -U USER, --USER USER  Run as USER
  -G GROUP, --GROUP GROUP
                        Run as GROUP
  -C CONFIG, --CONFIG CONFIG
                        Full path to config file
  -d {SESSION,SYSTEM}, --DBUS {SESSION,SYSTEM}
                        which bus to use, SESSION is default
</pre>
###pellmoncli.py:

Interactive command line client with tab completion. Reading and writeing of setting values, and reading of measurement data.
<pre>
usage: pellmoncli.py [-h] {get,set,list,i}
</pre>

###pellmon.conf
Configuration values. 


##User installation:
    # Generate configure script
    ./autogen.sh
    # Configure for installation in home directory
    ./configure --prefix=/home/<user>/.local
    make
    make install
    # Start the daemons manually
    /home/<user>/.local/bin/pellmonsrv.py -C /home/<user>/.local/etc/pellmon/pellmon.conf start
    /home/<user>/.local/bin/pellmonweb.py -C /home/<user>/.local/etc/pellmon/pellmon.conf -D
    # Stop the daemons manually
    kill $(cat /tmp/pellmonsrv.pid)
    kill $(cat /tmp/pellmonweb.pid)
###Uninstall
    make uninstall


##System installation:
    # Add system users
    sudo adduser --system --group --no-create-home pellmonsrv
    sudo adduser --system --group --no-create-home pellmonweb
    # Give the server access to the serial port
    sudo adduser pellmonsrv dialout
    ./autogen.sh
    # Configure for running as system users
    ./configure --with-user_srv=pellmonsrv --with-user_web=pellmonweb --sysconfdir=/etc
    make
    sudo make install
    # Activate pellmon dbus system bus permissions
    sudo service dbus reload
    # Start the daemons manually
    sudo service pellmonsrv start
    sudo service pellmonweb start
    # Or add them to init so they are started at boot
    sudo update-rc.d pellmonsrv defaults
    sudo update-rc.d pellmonweb defaults
###Uninstall
    sudo make uninstall
    # Remove from init if you added them
    sudo update-rc.d pellmonsrv remove
    sudo update-rc.d pellmonweb remove
    
##Dependencies:
<pre>
rrdtool, python-serial, python-cherrypy3, python-dbus, python-mako, python-gobject, python-simplejson
</pre>

##Build dependencies:
<pre>
autoconf
</pre>

##Plugin specific dependencies:
### OWFS
<pre>
owfs python-ownet
</pre>

