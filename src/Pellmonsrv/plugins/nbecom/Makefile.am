nobase_nbecom_PYTHON = \
	__init__.py \
	nbeprotocol/__init__.py \
	nbeprotocol/langmap.py \
	nbeprotocol/language.py \
	nbeprotocol/protocol.py \
	nbeprotocol/protocolexceptions.py \
	nbeprotocol/frames.py \
	nbeprotocol/directories.py

nbecomdir = $(pythondir)/Pellmonsrv/plugins/nbecom

dist_nbecomdata_DATA = nbeprotocol/language/lang.uk.prop

nbecomdatadir = $(datadir)/Pellmonsrv/plugins/nbecom/

do_substitution = $(SED) -e 's,[@]datadir[@],$(datadir),g' \
	-e 's,[@]localstatedir[@],$(localstatedir),g'

nbeprotocol/directories.py: nbeprotocol/directories.py.in Makefile
	mkdir -p nbeprotocol
	$(do_substitution) < $< > $@

EXTRA_DIST = \
	nbeprotocol/directories.py.in

CLEANFILES = \
	nbeprotocol/directories.py

uninstall-hook:
	rm -f nbeprotocol/directories.py
	rm -f nbeprotocol/directories.pyc
