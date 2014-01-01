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

AC_CONFIG_FILES([ \
Makefile \
initscript/Makefile \
data/Makefile \
src/Makefile \
src/Pellmonsrv/Makefile \
src/Pellmonsrv/yapsy/Makefile \
src/Pellmonsrv/plugins/Makefile \
src/Pellmonsrv/plugins/testplugin/Makefile \
src/Pellmonsrv/plugins/scottecom/Makefile \
src/Pellmonsrv/plugins/raspberrygpio/Makefile \
src/Pellmonsrv/plugins/customalarms/Makefile \
src/Pellmonsrv/plugins/calculate/Makefile \
src/Pellmonsrv/plugins/owfs/Makefile \
src/Pellmonsrv/plugins/silolevel/Makefile \
src/Scotteprotocol/Makefile \
src/Pellmonweb/Makefile ])

AC_OUTPUT
