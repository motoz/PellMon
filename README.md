PellMon
=======

Bio comfort / scotte / woody pellet burner - communication, setting and monitoring

Contains:

pellmonsrv.py:
Communication daemon. Implements a DBUS interface for reading and writing setting values and reading of measurement data. Optionally handles handles logging of measurement data to an RRD database. 

usage: pellmonsrv [-h] [-P PIDFILE] [-U USER] [-G GROUP] [-C CONFIG] [-D {SESSION,SYSTEM}]
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

pellmonweb.py:
Webserver and webapp, plotting of measurement, calculated consumption and data and parameter reading/writing.

usage: pellmonweb [-h] [-D] [-P PIDFILE] [-U USER] [-G GROUP] [-C CONFIG] [-d {SESSION,SYSTEM}]

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

pellmoncli.py:
Interactive command line client with tab completion. Reading and writeing of setting values, and reading of measurement data.

usage: pellmoncli [-h] {get,set,list,i}

pellmon.conf
Setting values.

User installation:
    ./autogen.sh
    ./configure.sh --prefix=/home/<user>/.local
    make
    make install
    /home/<user>/.local/bin/pellmonsrv -C /home/<user>/.local/etc/pellmon/pellmon.conf start
    /home/<user>/.local/bin/pellmonsrv -C /home/<user>/.local/etc/pellmon/pellmon.conf -D

System installation:
    to be documented...

Dependencies:
rrdtool, python-serial, python-cherrypy3, python-dbus, python-mako, python-gobject, python-simplejson

Build dependencies:
autoconf
