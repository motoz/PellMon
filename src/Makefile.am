SUBDIRS = Pellmonsrv Pellmonweb Scotteprotocol conf.d

bin_SCRIPTS = pellmonsrv pellmonweb pellmoncli.py
CLEANFILES = \
	pellmon.conf

confdir = $(sysconfdir)/pellmon
dist_conf_DATA = pellmon.conf

EXTRA_DIST = \
	pellmon.conf.in

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

%.conf: %.conf.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(srcdir)/$@

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	chown $(user_srv) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonweb
	chown $(user_web) $(DESTDIR)$(localstatedir)/log/pellmonweb
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/lib/pellmon
	chown $(user_srv) $(DESTDIR)$(localstatedir)/lib/pellmon

