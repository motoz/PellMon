SUBDIRS = plugins yapsy

srv_PYTHON = \
	daemon.py \
	pellmonsrv.py \
	plugin_categories.py \
	database.py \
	__init__.py

nodist_srv_PYTHON = \
	version.py \
	directories.py

CLEANFILES = \
	version.py \
	version.pyc \
	version.pyo \
	directories.py \
	directories.pyc \
	directories.pyo

EXTRA_DIST = \
	version.py.in \
	directories.py.in


srvdir = $(pythondir)/Pellmonsrv

do_substitution = $(SED) -e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]datadir[@],$(datadir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

%: %.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@


