AC_INIT([PellMon], [0.1])

AM_INIT_AUTOMAKE([foreign])
AM_PATH_PYTHON([2.7])

AC_PROG_MKDIR_P

AC_ARG_WITH([user_srv],
	AS_HELP_STRING([--with-user_srv=USER], [system user for pellmonsrv]),
	[],
	[with_user_srv=$(whoami)])

AC_SUBST([user_srv], [$with_user_srv])

AC_ARG_WITH([user_web],
	AS_HELP_STRING([--with-user_web=USER], [system user for pellmonweb]),
	[],
	[with_user_web=$(whoami)])

AC_SUBST([user_web], [$with_user_web])

AC_CONFIG_FILES([Makefile initscript/Makefile data/Makefile src/Makefile src/srv/Makefile src/web/Makefile])

AC_OUTPUT
