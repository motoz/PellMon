SUBDIRS = srv web

bin_SCRIPTS = pellmonsrv.py pellmonweb.py pellmoncli.py
CLEANFILES = $(bin_SCRIPTS)

sysconf_DATA = pellmon.conf

web_PYTHON = \
	pellmonweb.py 

webdir = $(pythondir)

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

pellmon.conf: pellmon.conf.in Makefile
	$(do_substitution) < $(srcdir)/pellmon.conf.in > pellmon.conf

