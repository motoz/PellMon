# Change Log
All notable changes to this project will be documented in this file.

## [0.7.0-beta7] 2017-01-22
### Added
- Plugin Heatingcircuit. Controls the heating circuit mixing valve according to outside temperature
- Plugin NBEcom for NBE V7/V13 pellet burners with ethernet connection. The plugin depends on python-crypto from the debian archive and xtea, which can be installed with pip
- Plugin Openweathermap. Read current temperature, wind speed, wind direction and humidity at your location from openweathermap.com and calculate apparent temperature from those. Depends on pyowm which can be installed with pip.
- Plugin Exec. Runs external commands on item read/write.
- Configure option `--enable-debug` makes it easy to set up the project to run directly from source when developing

### Changed
- Plugin interface to the database redesigned
- Graph plugin layout changed, eg. bootstrap buttons used for going back and forward

### Fixed
- Issue 71 fixed. Power calculated by the pelletcalc plugin could be > 0 while the burner is off if timer mode was used.
- Onewire plugin fixed, was broken since 0.7.0~beta1

## [0.6.1] - 2016-01-22
### Added
- Shell command line completion for pellmoncli
- debian package

### Changed
- New dependency: python-argcomplete
- plugin settins moved to a central sqlite database, pellmon-settings.db, in the same folder as the rrd database. Old settings are migrated automatically

## [0.5.0] - 2015-11-30
### Added
- Onewire plugin, reads onewire sensor data from /sys/bus/w1/devices/

## [0.4.0] - 2015-11-26
### Added
- pellmonconf, a web based text editor for the configuration files
- Cleaning plugin, keeps track of when the boiler needs cleaning

## [0.3.0] - 2015-11-15
### Added
- ScotteCom plugin support for V4 control boxes older than 4.17

## [0.2.0] - 2015-11-05
### Added
- The state tracker in the PelletCalc plugin has configurable parameters for every state change and can also be turned off completely, which removes the 'power_kW', 'mode' and 'alarm' items.
- The PelletCalc plugin has a configuration setting for which type of events to log

## [0.1.0] - 2015-11-01
### Added
- Version number and change log

### Changed
- The default configuration is split up in conf.d and conf.d/plugins directory with the `config_dir` directive in pellmon.conf

### Fixed
- The OWFS plugin did not work with the default owserver configuration in debian jessie.
The fix adds a new dependency on `pyownet`

