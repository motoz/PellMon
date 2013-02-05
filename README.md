PellMon
=======

Bio comfort / scotte / woody pellet burner - communication, setting and monitoring

Tested on a raspberry pi with debian


Contains: 

pellmonsrv.py:
Communication daemon. Implements a DBUS interface for reading and writing setting values and read measurement data. Also handles handles logging of measurement data to an RRD database. Usage: pellmonsrv.py start

pellmoncli.py:
Interactive command line client with tab completion. Uses the DBUS interface to read and write setting values, and read measurement data. 

pellmonwebb.py:
Implements a webbserver showing a graph of selected measurement data from the RRD database.

pellmon.conf
setting values, edit as desired

pellmon_dbus.conf
should be copied to /etc/dbus_1/system.d/ to allow pellmonsrv running as user "pi" to implement the DBUS interface on the system bus, edit the file to match the user name

html/index.html
template for the webb interface

dependencies:
rrdtool, python-cherrypy3, python-dbus, python-moko, python-gobject
(and maybe something more I forgot)


