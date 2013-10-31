# This file is part of pellmon.
#
# Pellmon is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Pellmon is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with pellmon; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA.

initddir = $(sysconfdir)/init.d

EXTRA_DIST = \
	pellmonsrv.in \
	pellmonweb.in


initd_SCRIPTS = \
	pellmonsrv \
	pellmonweb

CLEANFILES = \
	pellmonsrv \
	pellmonweb

pellmonsrv: pellmonsrv.in Makefile
	sed \
		-e 's,[@]user_srv[@],$(user_srv),g' \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]confdir[@],$(sysconfdir)/pellmon,g' \
		-e 's,[@]libdir[@],$(libdir),g' \
		$< > $@
	chmod +x $@

pellmonweb: pellmonweb.in Makefile
	sed \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]user_web[@],$(user_web),g' \
		-e 's,[@]confdir[@],$(sysconfdir)/pellmon,g' \
		$< > $@
	chmod +x $@

