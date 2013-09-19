SUBDIRS = srv web

bin_SCRIPTS = pellmonsrv.py pellmonweb.py pellmoncli.py
CLEANFILES = \
	$(bin_SCRIPTS) \
	pellmon.conf

confdir = $(sysconfdir)/pellmon
conf_DATA = pellmon.conf

EXTRA_DIST = \
	pellmonsrv.py \
	pellmoncli.py \
	pellmon.conf.in

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

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmon
	chown $(user_srv) $(DESTDIR)$(localstatedir)/log/pellmon
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/lib/pellmon
	chown $(user_srv) $(DESTDIR)$(localstatedir)/lib/pellmon

