SUBDIRS = Pellmonsrv Pellmonweb Scotteprotocol conf.d

bin_SCRIPTS = pellmonsrv pellmonweb pellmoncli pellmonconf

CLEANFILES = \
	pellmon.conf \
	pellmonconf \
	pellmoncli

confdir = $(sysconfdir)/pellmon

nodist_conf_DATA = pellmon.conf

EXTRA_DIST = \
	pellmon.conf.in \
	pellmoncli.in \
	pellmonsrv \
	pellmonweb \
	pellmonconf.in

do_substitution = $(SED) -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

%.conf: %.conf.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@

pellmoncli: pellmoncli.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@
	chmod +x $@

pellmonconf: pellmonconf.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@
	chmod +x $@

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	chown $(user_srv) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonweb
	chown $(user_web) $(DESTDIR)$(localstatedir)/log/pellmonweb
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/lib/pellmon
	chown $(user_srv) $(DESTDIR)$(localstatedir)/lib/pellmon

##install-exec-hook:
##	activate-global-python-argcomplete
