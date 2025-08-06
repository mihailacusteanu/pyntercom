# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Edge detection for call detection to prevent continuous triggering
- 5-second debouncing logic to prevent duplicate MQTT notifications
- Internal pull-up resistor support for reliable GPIO operation
- Comprehensive debug logging for all system operations
- Enhanced MQTT message handling with detailed debug information
- ESP12F relay board compatibility documentation

### Changed

- **BREAKING**: Switched call detection from GPIO 14 to GPIO 4 for better hardware compatibility
- Improved call detection reliability with edge-triggered logic (False→True transitions only)
- Enhanced debouncing from basic timing to proper time-based calculation
- Updated documentation to reflect new GPIO configuration and features

### Fixed

- Call detection reliability issues causing MQTT spam
- GPIO floating pin problems by using internal pull-up resistor
- Debouncing logic using correct time units (seconds vs milliseconds)
- Hardware compatibility issues with ESP12F relay boards

### Technical Details

- GPIO 4 supports internal pull-up resistors (GPIO 14, 16, 5 had compatibility issues)
- Edge detection prevents continuous GPIO readings from triggering multiple events
- Active-low call detection: HIGH (3.3V) = no call, LOW (0V/GND) = call detected
- MQTT topics unchanged for backward compatibility

## [Previous Versions]

- Initial implementation with basic call detection and MQTT integration
