# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 17/02-2020

### Added

- Support for NEAT UE Policy System

### Changed

- Network Functions DB instead of SST
- Slice Mapping chooses the most suitable Functions from the database
- Removed PDU db
- Improved Slice Deletion process

## [2.1.1] - 03/02-2020

### Added

- Support (API and DB) for external Policy System Engine

### Changed

- Required fields on json schema
- Readmec file
- GST Terminology
- Wiki

## [2.1.0] - 16/01/2020

### Added

- Kafka and Zookeeper Containers | Split katana-mngr to 2 processes-containers: katana-nbi and katana-mngr | Created Kafka producers & consumer to exchange messages between containers
- Required field for VIM, NFVO, WIM, EMS, PDU components
- Check for that the required fields stay the same when update one of these components
- Index in mongo to ID field for these components to avoid duplicate IDs
- Support for "test" types of EMS and WIM 
- This changelog

### Changed

- Appearance of "katana sst ls" command
- Customized katana-cli to print http body on httperror case
- Fixed bugs on slice deletion process

## [2.0.0] - 08/01/2020

### Added

- New Information model for slice creation (GST)
- Slice mapping process | Create NEST based on GST and supported SST
- Added Supported SST instead of Registered Services
- Hunab-readable Unique ID for each component
- New Resource API per location

### Changed

- Upgrade swagger to Open APIs 3.0.1
- New example config files
- Redesigned the slice deletion process
- VIM admin account bug fixed
- Katana CLI ls output appearance
