# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- Version number and change log

### Changed
- The default configuration is split up in conf.d and conf.d/plugins directory with the `config_dir` directive in pellmon.conf

### Fixed
- The OWFS plugin did not work with the default owserver configuration in debian jessie.
The fix adds a new dependency on `pyownet`

