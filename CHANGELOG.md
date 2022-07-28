# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## 2.0.3 - 2022-07-19

### Fixed

- Fixed an issue where the library would get stuck if it needed to create a new
  session in order to continue (reported and contributed by @BiochemLouis in #5
  and #6)

## 2.0.2 - 2022-04-04

This is a release to bump the pip package version, to correct the previous PyPI release not containing the correct revision of code. No other changes.

## 2.0.1 - 2022-01-11

### Fixed

- Fixed an issue with empty (unchanged) updates (#2)

## 2.0.0 - 2021-11-19

### Changed

- Updated library to use new AppConfig Data API

### Removed

- Removed the `client_id` parameter for the AppConfigHelper class as it is no
  longer used by the API
- Removed the `config_version` property, as it is no longer returned by the API

## 1.1.0 - 2020-11-04

### Added

- `raw_content` and `content_type` properties

## 1.0.0 - 2020-10-20

- Initial release
