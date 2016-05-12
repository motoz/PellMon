SUBDIRS = plugins yapsy

srv_PYTHON = \
	daemon.py \
	pellmonsrv.py \
	plugin_categories.py \
	database.py \
	__init__.py \
	version.py \
	directories.py


EXTRA_DIST = \
	version.py.in \
	directories.py.in

CLEANFILES = \
	version.py \
	directories.py

srvdir = $(pythondir)/Pellmonsrv

do_substitution = $(SED) -e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]datadir[@],$(datadir),g' \
	-e 's,[@]localstatedir[@],$(pellmonlocalstatedir),g'

%: %.in Makefile
	$(do_substitution) < $< > $@

uninstall-hook:
	rm -f version.py
	rm -f version.pyc
	rm -f directories.py
	rm -f directories.pyc
