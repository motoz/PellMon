AC_INIT([PellMon], [0.1])

AM_INIT_AUTOMAKE([foreign])
AM_PATH_PYTHON([2.7])

PKG_PROG_PKG_CONFIG([0.0])

AC_ARG_WITH([dbuspolicydir],
	AS_HELP_STRING([--with-dbuspolicydir=DIR], [D-Bus policy directory]),
	[],
	[with_dbuspolicydir=$($PKG_CONFIG --variable=sysconfdir dbus-1)/dbus-1/system.d])

AC_SUBST([dbuspolicydir], [$with_dbuspolicydir])

AC_CONFIG_FILES([Makefile initscript/Makefile data/Makefile src/Makefile src/srv/Makefile src/web/Makefile])

AC_OUTPUT
