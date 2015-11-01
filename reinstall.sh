echo "using sudo, password might be requested"

echo "stopping daemons"
sudo service pellmonsrv stop
sudo service pellmonweb stop

echo "make pellmon_conf directory"
mkdir -p  pellmon_conf

echo "backup pellmon configuration"
cp -r /etc/pellmon/ pellmon_conf/ || exit 1

echo "build pellmon"
make --no-print-directory || exit 1

echo "install pellmon"
sudo make --no-print-directory install || exit 1

echo "restore configuration"
sudo cp -r pellmon_conf/pellmon/ /etc/ || exit 1

echo "reload init (systemd might want this)"
sudo update-rc.d pellmonsrv defaults
sudo update-rc.d pellmonweb defaults

echo "start daemons"
sudo service pellmonsrv start || exit 1
sudo service pellmonweb start || exit 1
