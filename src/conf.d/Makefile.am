CLEANFILES = \
	database.conf \
	webinterface.conf

confdir = $(sysconfdir)/pellmon/conf.d

nobase_nodist_conf_DATA = \
	webinterface.conf \
	database.conf 

nobase_dist_conf_DATA = \
	email.conf \
	enabled_plugins.conf \
	plugins/owfs.conf \
	plugins/calculate.conf \
	plugins/customalarms.conf \
	plugins/raspberrygpio.conf \
	plugins/scottecom.conf \
	plugins/testplugin.conf \
	plugins/onewire.conf \
	plugins/pelletcalc.conf \
	plugins/nbecom.conf

EXTRA_DIST = \
	database.conf.in \
	webinterface.conf.in

do_substitution = $(SED) -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
	-e 's,[@]confdir[@],$(confdir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

%.conf: %.conf.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@

