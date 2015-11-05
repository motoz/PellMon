# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- The state tracker in the PelletCalc plugin has configurable parameters for every state change and can also be turned off completely, which removes the 'power_kW', 'mode' and 'alarm' items.

## [0.1.0] - 2015-11-01
### Added
- Version number and change log

### Changed
- The default configuration is split up in conf.d and conf.d/plugins directory with the `config_dir` directive in pellmon.conf

### Fixed
- The OWFS plugin did not work with the default owserver configuration in debian jessie.
The fix adds a new dependency on `pyownet`

