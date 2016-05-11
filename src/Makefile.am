SUBDIRS = Pellmonsrv Pellmonweb Scotteprotocol conf.d

bin_SCRIPTS = pellmonsrv pellmonweb pellmoncli pellmonconf

CLEANFILES = \
	pellmon.conf \
	pellmonconf \
	pellmoncli


if DEBUG
confdir = $(CURDIR)/conf.d.dev
export confdir = $(CURDIR)/pellmon
export pellmonconfdir = $(CURDIR)/conf.d.dev
export pellmonlocalstatedir = $(CURDIR)/dev_var
else
confdir = $(sysconfdir)/pellmon
export pellmonconfdir = $(sysconfdir)/pellmon/conf.d
export confdir = $(sysconfdir)/pellmon
export pellmonconfdir = $(sysconfdir)/pellmon/conf.d
export pellmonlocalstatedir = $(localstatedir)
endif

nodist_conf_DATA = pellmon.conf

EXTRA_DIST = \
	pellmon.conf.in \
	pellmoncli.in \
	pellmonconf.in \
	pellmonweb \
	pellmonsrv

do_substitution = $(SED) -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]pellmonconfdir[@],$(pellmonconfdir),g' \
	-e 's,[@]datadir[@],$(datadir),g' \
	-e 's,[@]localstatedir[@],$(pellmonlocalstatedir),g'

%.conf: %.conf.in Makefile
	$(do_substitution) < $< > $@

pellmoncli: pellmoncli.in Makefile
	$(do_substitution) < $< > $@
	chmod +x $@

pellmonconf: pellmonconf.in Makefile
	$(do_substitution) < $< > $@
	chmod +x $@

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	chown $(user_srv) $(DESTDIR)$(localstatedir)/log/pellmonsrv
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/log/pellmonweb
	chown $(user_web) $(DESTDIR)$(localstatedir)/log/pellmonweb
	$(MKDIR_P) $(DESTDIR)$(localstatedir)/lib/pellmon
	chown $(user_srv) $(DESTDIR)$(localstatedir)/lib/pellmon

distclean-local:
	rm -rf conf.d.dev/

##install-exec-hook:
##	activate-global-python-argcomplete
