web_PYTHON = \
	pellmonweb.py \
	pellmonconf.py \
	auth.py \
	consumption.py \
	logview.py \
	__init__.py 

nodist_web_PYTHON = \
	version.py

CLEANFILES = \
	version.py

EXTRA_DIST = \
	version.py.in

webdir = $(pythondir)/Pellmonweb

nobase_dist_foohtml_DATA = \
	media/js/spin.js \
	media/js/logview.js \
	media/js/index.js \
	media/js/parameters.js \
	media/js/websocket.js \
	media/js/reconnectingwebsocket.js \
	media/js/consumption.js \
	media/js/source.js \
	media/css/pellmon.css \
	media/css/pellmonconf.css \
	media/css/pellmonconf_print.css \
	media/img/pellmon.svg \
	media/img/spinner.gif \
	media/img/system.svg \
	media/img/system_matene.svg \
	media/img/system_nbe.svg \
	media/img/system_nbe_2w.svg \
	media/img/system_nbe_3w.svg \
	media/img/apple-touch-icon-114x114.png \
	media/img/apple-touch-icon-120x120.png \
	media/img/apple-touch-icon-144x144.png \
	media/img/apple-touch-icon-152x152.png \
	media/img/apple-touch-icon-57x57.png \
	media/img/apple-touch-icon-60x60.png \
	media/img/apple-touch-icon-72x72.png \
	media/img/apple-touch-icon-76x76.png \
	media/img/apple-touch-icon.png \
	media/img/apple-touch-icon-precomposed.png \
	media/img/browserconfig.xml \
	media/img/favicon-160x160.png \
	media/img/favicon-16x16.png \
	media/img/favicon-196x196.png \
	media/img/favicon-32x32.png \
	media/img/favicon-96x96.png \
	media/img/favicon.ico \
	media/img/mstile-144x144.png \
	media/img/mstile-150x150.png \
	media/img/mstile-310x150.png \
	media/img/mstile-310x310.png \
	media/img/mstile-70x70.png \
	media/jquery/jquery.js \
	media/jquery/jquery.min.js \
	media/bs3/fonts/glyphicons-halflings-regular.svg \
	media/bs3/fonts/glyphicons-halflings-regular.woff \
	media/bs3/fonts/glyphicons-halflings-regular.eot \
	media/bs3/fonts/glyphicons-halflings-regular.ttf \
	media/bs3/js/bootstrap.js \
	media/bs3/js/bootstrap.min.js \
	media/bs3/css/bootstrap-theme.min.css \
	media/bs3/css/bootstrap.css \
	media/bs3/css/bootstrap-theme.css \
	media/bs3/css/bootstrap.min.css \
	media/flot/jquery.flot.js \
	media/flot/jquery.flot.time.js \
	media/flot/jquery.flot.resize.js \
	media/flot/jquery.flot.navigate.js \
	media/codemirror/LICENSE \
	media/codemirror/lib/codemirror.css \
	media/codemirror/lib/codemirror.js \
	media/codemirror/mode/clike/clike.js \
	media/codemirror/mode/clike/index.html \
	media/codemirror/mode/clike/scala.html \
	media/codemirror/mode/properties/index.html \
	media/codemirror/mode/properties/properties.js \
	media/codemirror/mode/simple/simple.js \
	html_conf/layout.html \
	html_conf/source.html \
	html/layout.html \
	html/parameters.html \
	html/consumption.html \
	html/loglines.html \
	html/index.html \
	html/login.html \
	html/events\
	html/graph\
	html/systemimage\
	html/logview.html \
	html/about.html

foohtmldir = $(pythondir)/Pellmonweb

do_substitution = $(SED) -e 's,[@]VERSION[@],$(VERSION),g'

%: %.in Makefile
	$(do_substitution) < $(srcdir)/$< > $(builddir)/$@


