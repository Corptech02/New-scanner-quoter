# Changelog

All notable changes to the Multi-Tab Claude Voice Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-08-11

### Added
- Per-request stats display (timer and tokens reset after each response)
- Terminal monitor integration for debugging
- Processing indicator (⏳) during active Claude requests
- Token formatting with k-notation (1.0k, 2.5k, etc.)

### Changed
- Stats now work like Claude AI - showing only current request metrics
- Timer only counts during Claude processing time
- Improved stats box UI with grid layout matching exact specifications

### Fixed
- Duplicate thread creation issue in send_command
- Thread synchronization problems causing stats to stop
- Stats were showing cumulative totals instead of per-request

## [2.0.0] - 2025-08-10

### Added
- Multi-tab support (up to 4 simultaneous Claude sessions)
- Real-time voice interaction with edge-tts
- WebSocket-based real-time updates
- Session state management per tab
- Visual indicators for active/unread tabs
- HTTPS support with self-signed certificates

### Changed
- Complete rewrite from single-session to multi-tab architecture
- Migrated from HTTP polling to WebSocket communication
- Enhanced UI with exact replica of Claude.ai design

## [1.0.0] - 2025-08-09

### Added
- Initial release with single session support
- Basic voice input/output functionality
- Simple web interface
- Claude API integration