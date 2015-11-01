SUBDIRS = plugins yapsy

srv_PYTHON = \
	daemon.py \
	pellmonsrv.py \
	plugin_categories.py \
	__init__.py \
	version.py

srvdir = $(pythondir)/Pellmonsrv

do_substitution = $(SED) -e 's,[@]VERSION[@],$(VERSION),g'

%: %.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(srcdir)/$@

