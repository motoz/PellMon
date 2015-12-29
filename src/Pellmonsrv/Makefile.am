SUBDIRS = plugins yapsy

srv_PYTHON = \
	daemon.py \
	pellmonsrv.py \
	plugin_categories.py \
	__init__.py

nodist_srv_PYTHON = \
	version.py

CLEANFILES = \
	version.py

EXTRA_DIST = \
	version.py.in


srvdir = $(pythondir)/Pellmonsrv

do_substitution = $(SED) -e 's,[@]VERSION[@],$(VERSION),g'

%: %.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@

