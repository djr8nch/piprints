# PiPrints

<p align="center">
  <img src="docs/assets/banner.png" alt="PiPrints Banner" width="100%">
</p>

<p align="center">
  <strong>📸 An open-source Raspberry Pi photo booth platform.</strong>
</p>

<p align="center">
  Build your own customizable photo booth using a Raspberry Pi, camera module, and printer.
</p>

<p align="center">
  <img src="docs/assets/logo.png" alt="PiPrints Logo" width="180">
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Raspberry%20Pi-C51A4A?logo=raspberry-pi&logoColor=white">
  <img alt="Status" src="https://img.shields.io/badge/Status-Early%20Development-orange">
</p>

---

## Overview

**PiPrints** is an open-source photo booth platform built for Raspberry Pi. The goal is to provide a polished, modular, and customizable experience that anyone can build using affordable hardware.

Whether you're building a booth for a wedding, birthday, graduation, makerspace, or simply as a fun Raspberry Pi project, PiPrints is designed to be easy to use, easy to modify, and enjoyable to contribute to.

The project emphasizes:

- Modular software architecture
- Comprehensive documentation
- Hardware flexibility
- Customizable themes
- Multiple printer backends
- Open-source collaboration

---

# Project Status

> **Early Development**

PiPrints is currently in active development.

The initial milestone focuses on building a complete end-to-end experience:

- Camera Preview
- Countdown Timer
- Photo Capture
- Thermal Printing
- Session Management
- Image Processing Pipeline

Future versions will introduce additional printer support, themes, plugins, QR code sharing, GIF mode, and more.

---

# Features

### Current

- Raspberry Pi Camera integration
- Thermal printer support
- Session management
- Modular project architecture

### Planned

- Photo strip generation
- Theme engine
- QR code downloads
- GIF mode
- Touchscreen interface
- Plugin system
- DSLR support
- Cloud backups
- Analytics dashboard

---

# Roadmap

## Version 0.1 — MVP

- [ ] Camera preview
- [ ] Countdown timer
- [ ] Capture session
- [ ] Thermal printer integration
- [ ] Basic UI
- [ ] Documentation

## Version 0.5

- [ ] Theme support
- [ ] Configuration system
- [ ] Improved UI
- [ ] Image filters

## Version 1.0

- [ ] Stable release
- [ ] Complete documentation
- [ ] Installation scripts
- [ ] Plugin API
- [ ] Public release

---

# Planned Architecture

```text
                 PiPrints

                     │
     ┌───────────────┴───────────────┐
     │                               │
     ▼                               ▼
 User Interface              Session Manager
                                     │
      ┌──────────────┬───────────────┼──────────────┐
      ▼              ▼               ▼              ▼
 Camera        Image Pipeline     Printer      Storage
```

The architecture is intentionally modular so that cameras, printers, layouts, themes, and future plugins can evolve independently.

---

# Repository Structure

```text
PiPrints/
│
├── .github/
├── assets/
├── docs/
├── examples/
├── scripts/
├── src/
│   └── piprints/
├── tests/
│
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

---

# Planned Hardware

### Primary Development Platform

- Raspberry Pi 4
- Raspberry Pi Camera Module 3
- Mini Thermal Printer
- Arcade Push Button

### Future Hardware Support

- Raspberry Pi 5
- Canon SELPHY printers
- DSLR cameras
- Touchscreen displays
- Additional GPIO accessories

---

# Documentation

Documentation is located inside the `docs/` directory.

Planned documentation includes:

- Installation Guide
- Hardware Guide
- Development Guide
- Architecture
- API Reference
- Troubleshooting
- Design Documents

---

# Contributing

Contributions are welcome!

Whether you're fixing bugs, improving documentation, designing themes, or adding support for new hardware, we'd love your help.

Contribution guidelines will be available in **CONTRIBUTING.md**.

---

# Project Vision

PiPrints aims to become the easiest and most flexible open-source Raspberry Pi photo booth platform.

Rather than being a single application, PiPrints is designed as a modular platform that allows makers, students, educators, photographers, and developers to build customized photo booth experiences using inexpensive hardware.

The project prioritizes:

- Clean architecture
- Excellent documentation
- Extensibility
- Accessibility
- Long-term maintainability

---

# Development Status

| Component | Status |
|-----------|--------|
| Repository Setup | ✅ |
| Project Planning | ✅ |
| Documentation | 🚧 |
| Architecture | 🚧 |
| Camera Module | ⏳ |
| UI | ⏳ |
| Printing | ⏳ |
| Themes | ⏳ |
| Testing | ⏳ |

Legend:

- ✅ Complete
- 🚧 In Progress
- ⏳ Planned

---

# License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.

---

<p align="center">
Built with ❤️ using Raspberry Pi, Python, and open-source software.
</p>
