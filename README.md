PellMon
=======
![logo](https://raw.github.com/motoz/PellMon/master/src/Pellmonweb/media/img/favicon-160x160.png)

PellMon is logging, monitoring and configuration solution for pellet burners. It consists of a backend server daemon, which
uses RRDtool as a logging database, and a frontend daemon providing a responsive mobile friendly web based user interface. 
Additionally there is a command line tool for interfacing with the server, and web based configuration tool.
PellMon can communicate directly with a supported pellet burner, or it can use a feeder-auger revolution counter as
base for pellet consumption calculation.

PellMon uses plugins to provide data about your burner. The most fully featured plugin is **ScotteCom**, which enables communication 
with a NBE scotte/woody/biocomfort V4, V5 or V6 pellet burner. It gives you access to almost all configuration parameters 
and measurement data, and also handles logging of alarms and mode/setting changes.

The plugin system makes it easy to add custom plugins for extended functionality, a 'template' plugin is provided as an example
along with the other preinstalled plugins:

**PelletCalc** Calculated power value and pellet consumption from a feeder auger counter.

**RaspberryPi** Access inputs and outputs on the raspberry pi single board computer. One input can be configured
as a counter to provide a base for pellet consumption calculation. It also provides general I/O, and a tachometer input that can be used
to measure the blower speed, by interfacing to the blowers tacho output or by using an optical detector.

**OWFS** Communicate with an owserver. Can be used to read onewire sensors, for instance temperature. It can also use a 
onewire input (ds2460 based) to count feeder auger revolutions for use with the PelletCalc plugin. 

**Consumption** Calculate and graph hourly, weekly, monthly and yearly fuel consumption.

**CustomAlarms** Create an unlimited number of limits to watch on available data, optionally send email when a limit is exceeded.

**Calculate** A simple script engine to to calcualate new values based on the existing data and automate things.

**SiloLevel** Calculate and graph the pellet silo level from the fill-up time to current time.

**Cleaning** Calculate how much fuel is burned since the boiler was last cleaned.

**Onewire** Read onewire sensor data using the kernel driver interface /sys/bus/w1/

Plugin documentation is found in the configuration file at plugins/plugin-name.conf

####Contains:

###pellmonsrv:
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

###pellmonweb:
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
###pellmoncli:

Interactive command line client with tab completion. Reading and writing of setting values, and reading of measurement data.

    usage: pellmoncli.py [-h] {get,set,list,i}

###pellmonconf:
Web based text editor for the configuration files
<pre>
pellmonconf -h
usage: pellmonconf [-h] [-P PORT] [-H HOST]

optional arguments:
  -h, --help            show this help message and exit
  -P PORT, --port PORT  Port number for webinterface, default 8083
  -H HOST, --host HOST  Host for webinterface, default 0.0.0.0
</pre>

###pellmon.conf
The default configuration is split up in several files in the conf.d directory using the directive `config_dir = /etc/pellmon/conf.d` in pellmon.conf.

##System installation:
    # Add system users
    sudo adduser --system --group --no-create-home pellmonsrv
    sudo adduser --system --group --no-create-home pellmonweb
    # Give the server access to the serial port
    sudo adduser pellmonsrv dialout
    # Create build system
    ./autogen.sh
    # Configure for running as system users
    ./configure --with-user_srv=pellmonsrv --with-user_web=pellmonweb --sysconfdir=/etc
    # Build PellMon
    make
    # Install PellMon
    sudo make install
    # Activate pellmon dbus system bus permissions
    sudo service dbus reload
    # Add them to init so they are started at boot
    sudo update-rc.d pellmonsrv defaults
    sudo update-rc.d pellmonweb defaults
    # Start the daemons manually, or reboot
    sudo service pellmonsrv start
    sudo service pellmonweb start
###Uninstall
    sudo make uninstall
    # Remove from init if you added them
    sudo update-rc.d pellmonsrv remove
    sudo update-rc.d pellmonweb remove

##User installation:
    # Generate configure script
    ./autogen.sh
    # Configure for installation in home directory
    ./configure --prefix=/home/<user>/.local
    make
    make install
    # Start the daemons manually
    /home/<user>/.local/bin/pellmonsrv.py -C /home/<user>/.local/etc/pellmon/pellmon.conf --PLUGINDIR /home/<user>/.local/lib/Pellmonsrv/plugins/ start
    /home/<user>/.local/bin/pellmonweb.py -C /home/<user>/.local/etc/pellmon/pellmon.conf -D
    # Stop the daemons manually
    kill $(cat /tmp/pellmonsrv.pid)
    kill $(cat /tmp/pellmonweb.pid)
###Uninstall
    make uninstall

##Dependencies:
    rrdtool python-serial python-cherrypy3 python-dbus python-mako python-gobject python-simplejson python-dateutil python-argcomplete

##Optional dependencies:
    python-ws4py
##Dependencies for plugins
###OWFS:
    pyownet

##Build dependencies:
    autoconf

