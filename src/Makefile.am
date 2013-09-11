SUBDIRS = srv web common

bin_SCRIPTS = pellmonsrv pellmonweb pellmoncli
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = pellmonsrv.in pellmonweb.in pellmoncli.in

sysconf_DATA = pellmon.conf

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

pellmon.conf: pellmon.conf.in Makefile
	$(do_substitution) < $(srcdir)/pellmon.conf.in > pellmon.conf

