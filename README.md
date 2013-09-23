PellMon
=======

Bio comfort / scotte / woody pellet burner - communication, setting and monitoring

####Contains:

###pellmonsrv.py:
Communication daemon. Implements a DBUS interface for reading and writing setting values and reading of measurement data. Optionally handles logging of measurement data to an RRD database. 
<pre>
usage: pellmonsrv.py [-h] [-P PIDFILE] [-U USER] [-G GROUP] [-C CONFIG] [-D {SESSION,SYSTEM}]
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
    ./autogen.sh
    # Configure for running as system users
    ./configure --with-user_srv=pellmonsrv --with-user_web=pellmonweb
    ./configure --with-user_srv=pellmonsrv --with-user_web=pellmonweb --sysconfdir=/etc
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
