# PiPrints Agent Instructions

## Project Overview

PiPrints is an open-source Raspberry Pi photo booth platform written in Python.

The project is designed specifically for Raspberry Pi hardware and is intended to become a highly modular, extensible, well-documented photo booth platform suitable for real-world use, open-source contribution, and long-term maintenance.

PiPrints should demonstrate professional software engineering practices rather than tutorial-style architecture.

When making implementation decisions, prioritize:

* maintainability
* readability
* modularity
* extensibility
* testability
* documentation quality
* clear architectural boundaries

Prefer a slightly more deliberate design over the shortest possible implementation, but avoid unnecessary abstraction and overengineering.

---

# Platform Assumptions

PiPrints is Raspberry Pi-first.

The primary runtime environment is:

* Raspberry Pi hardware
* 64-bit Raspberry Pi OS
* Python 3
* PySide6 for the graphical interface
* Raspberry Pi Camera Module using Picamera2
* Linux system services and hardware integrations where appropriate

Do not introduce cross-platform abstractions solely to support macOS or Windows unless doing so provides clear architectural value.

Hardware-specific functionality must remain isolated inside dedicated modules.

---

# Repository Structure

The project follows a `src` layout.

```text
PiPrints/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
│
├── assets/
│   ├── fonts/
│   ├── icons/
│   ├── logos/
│   ├── sounds/
│   └── themes/
│
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── assets/
│   ├── development/
│   ├── hardware/
│   └── screenshots/
│
├── examples/
│
├── scripts/
│   ├── install.sh
│   ├── run.sh
│   └── setup_service.sh
│
├── src/
│   └── piprints/
│       ├── __init__.py
│       ├── app.py
│       ├── bootstrap.py
│       │
│       ├── booth/
│       ├── camera/
│       ├── config/
│       ├── imaging/
│       │   ├── layouts/
│       │   └── operations/
│       ├── input/
│       ├── printing/
│       ├── session/
│       ├── storage/
│       ├── themes/
│       ├── ui/
│       │   ├── screens/
│       │   └── widgets/
│       └── utils/
│
├── tests/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

Do not move responsibilities between these modules casually.

If a new subsystem is required, first determine whether it belongs naturally inside an existing package before creating a new top-level package.

---

# Architectural Principles

## High Cohesion

Every module should have one clear responsibility.

Examples:

* camera code belongs in `camera/`
* printing code belongs in `printing/`
* image processing belongs in `imaging/`
* UI components belong in `ui/`
* session state belongs in `session/`
* persistent storage belongs in `storage/`
* application orchestration belongs in `booth/`

Avoid God classes and modules that accumulate unrelated behavior.

---

## Low Coupling

Subsystems should know as little as possible about one another.

Examples:

* UI code should not know how a printer works.
* Printer implementations should not know how the UI works.
* Camera implementations should not know how captured images are processed.
* Image processors should not know whether an image came from a camera, file, or test fixture.
* Booth logic should depend on abstractions rather than hardware-specific implementations.

Avoid importing concrete hardware implementations throughout the application.

---

# SOLID Principles

Apply SOLID principles where they improve maintainability.

## Single Responsibility Principle

A class should have one primary reason to change.

Do not combine hardware control, UI rendering, persistence, and workflow logic in one class.

## Open/Closed Principle

Prefer designs where additional implementations can be added without modifying unrelated existing code.

For example, adding a future printer implementation should not require rewriting booth workflow logic.

## Liskov Substitution Principle

Implementations of an abstraction must honor the behavior expected by callers.

## Interface Segregation Principle

Keep interfaces small.

Do not expose the entire capabilities of a third-party library simply because they are available.

Interfaces should represent what PiPrints actually needs.

## Dependency Inversion Principle

High-level application logic should depend on PiPrints-owned abstractions rather than low-level hardware libraries.

Concrete hardware implementations should be injected during application startup.

---

# Composition Over Inheritance

Prefer small composable objects over large inheritance hierarchies.

Inheritance is acceptable when there is a genuine substitutable abstraction, but do not use inheritance merely to reuse code.

Prefer:

```text
BoothController
    ├── Camera
    ├── Printer
    ├── SessionManager
    └── ImageProcessor
```

over a deeply inherited application hierarchy.

---

# Dependency Injection

Use lightweight constructor-based dependency injection where useful.

`bootstrap.py` should act as the application's composition root.

It is responsible for creating concrete implementations and wiring them together.

For example:

```python
camera = PiCamera(...)
printer = CupsPrinter(...)
storage = FileStorage(...)

booth = BoothController(
    camera=camera,
    printer=printer,
    storage=storage,
)
```

Avoid global service instances and hidden dependency lookups.

---

# Camera Architecture

Camera hardware must remain isolated inside `piprints.camera`.

Picamera2 is the Raspberry Pi camera implementation detail.

Do not import:

```python
from picamera2 import Picamera2
```

outside the camera package.

Higher-level code should communicate through a PiPrints-owned camera abstraction.

The camera abstraction should remain intentionally small and should expose only operations required by PiPrints.

Do not create a generic wrapper around every Picamera2 function.

Possible responsibilities include:

* start camera
* stop camera
* capture image
* provide preview frames when required

Autofocus, libcamera configuration, CSI details, and Raspberry Pi-specific behavior belong inside the camera implementation.

---

# Printing Architecture

Printing logic must remain inside `piprints.printing`.

The UI and booth workflow should not directly execute shell printing commands or depend on CUPS APIs.

Define a PiPrints-owned printer abstraction before adding multiple printer implementations.

Printer implementations should be replaceable without changing booth workflow code.

---

# Imaging Architecture

Image processing belongs in `piprints.imaging`.

This includes functionality such as:

* resizing
* cropping
* image composition
* overlays
* templates
* layouts
* filters
* borders
* photo-strip generation

Image processing functions should operate on images and configuration, not on camera or UI objects.

Prefer deterministic, testable transformations.

---

# UI Architecture

PiPrints uses PySide6.

UI code belongs inside `piprints.ui`.

The UI should display application state and forward user intent to application-level controllers or services.

Avoid placing business logic inside widgets or screens.

A screen should not:

* directly control camera hardware
* directly send print jobs
* manage filesystem persistence
* perform complex image processing
* own booth workflow state

UI components should remain replaceable without changing core business logic.

---

# Booth / Application Logic

The `booth` package owns the primary photo booth workflow.

It should coordinate subsystems rather than implement their internal behavior.

Examples of workflow responsibilities may include:

```text
Idle
↓
Start Session
↓
Countdown
↓
Capture
↓
Review
↓
Process
↓
Print / Save
↓
Complete
↓
Idle
```

A State pattern may be appropriate once booth workflow complexity justifies it.

Do not introduce the State pattern before meaningful state behavior exists.

---

# Design Patterns

Use design patterns only when they solve an actual architectural problem.

Patterns likely to be appropriate include:

* Strategy
* State
* Factory
* Adapter
* Observer
* Facade
* Dependency Injection

Potential examples:

### Strategy

Different:

* image layouts
* photo processors
* printing behavior
* capture behavior

### Factory

Creating configured implementations from application configuration.

### Adapter

Wrapping third-party or operating-system APIs behind PiPrints-owned interfaces.

Examples may include Picamera2 or CUPS integrations.

### Observer

Communicating application state changes to the UI without tightly coupling UI components to workflow internals.

Do not introduce patterns merely to make the project appear sophisticated.

Every pattern must reduce coupling, improve extensibility, or clarify responsibility.

---

# Code Quality

Prioritize readable code over clever code.

Functions should generally remain small and focused.

Avoid:

* deeply nested conditionals
* excessive boolean flags
* hidden side effects
* global mutable state
* giant utility modules
* premature abstraction
* unnecessary metaprogramming

Use descriptive names.

Prefer explicit behavior over surprising behavior.

Public classes and methods should have clear docstrings.

Type hints should be used consistently for public APIs and important internal boundaries.

---

# Exceptions and Error Handling

Prefer domain-specific exceptions when callers need to respond differently to particular failures.

Do not catch broad exceptions unless:

* cleanup is required
* the exception is re-raised
* the error is translated at an architectural boundary
* the application can meaningfully recover

Hardware failures must not crash the application without useful diagnostic information.

Error messages should contain enough context to troubleshoot Raspberry Pi hardware issues.

---

# Logging

Use Python logging for runtime diagnostics.

Do not rely on scattered `print()` statements in application code.

Useful log events include:

* application startup
* hardware initialization
* camera connection
* photo capture
* processing completion
* printer submission
* recoverable errors
* session start/end

Avoid logging sensitive or unnecessarily large data.

---

# Configuration

Runtime configuration belongs in `piprints.config`.

Do not scatter magic constants across modules.

Configuration may eventually include:

* camera settings
* countdown duration
* output directories
* printing options
* active theme
* selected layout
* UI settings

Configuration objects should be passed explicitly to components that require them.

---

# Testing Requirements

Testing is expected from the beginning.

Separate testing into three conceptual categories.

## Unit Tests

Unit tests should:

* avoid real hardware
* remain deterministic
* run quickly
* test individual business rules and transformations

Hardware dependencies should be replaceable with fakes or mocks.

## Integration Tests

Integration tests may verify cooperation between multiple PiPrints components.

They should still avoid physical hardware unless explicitly categorized otherwise.

## Hardware Validation

Hardware validation tests are Raspberry Pi-specific and may require:

* Camera Module
* printer
* GPIO
* display

Hardware tests must be clearly separated so standard test runs do not require physical hardware.

Never make the default CI test suite depend on Raspberry Pi hardware.

---

# Documentation Requirements

Documentation is a first-class feature.

When implementing a substantial feature, evaluate whether the following also need updates:

* `README.md`
* `docs/architecture/`
* `docs/development/`
* `docs/hardware/`
* `docs/api/`
* `CHANGELOG.md`

Architectural decisions should include rationale, especially when they introduce new abstractions or dependencies.

Documentation should explain not only how something works but why the architecture was chosen when that context would help contributors.

---

# Installation and Setup

PiPrints should be easy for a new contributor or user to install.

The long-term target is:

```bash
git clone <repository>
cd PiPrints
./scripts/install.sh
```

followed by:

```bash
./scripts/run.sh
```

Installation responsibilities must remain separated.

## `pyproject.toml`

Owns normal Python dependencies and project metadata.

## `scripts/install.sh`

Owns Raspberry Pi OS / system-level setup.

Examples include:

* apt packages
* camera dependencies
* OS-level libraries
* virtual environment setup
* application installation
* validation checks

## Documentation

`docs/development/` should explain what installation scripts do and how to troubleshoot them.

`docs/hardware/` should document physical hardware installation and validation.

The installation script should eventually be idempotent: running it multiple times should be safe.

Do not hide unexplained dependencies inside setup scripts.

---

# Raspberry Pi Camera Requirements

PiPrints targets the modern Raspberry Pi camera stack.

Do not rely on legacy Raspberry Pi camera APIs or deprecated `raspi-config` camera-enable instructions.

Use:

* Picamera2
* libcamera / rpicam tooling
* supported Raspberry Pi OS camera infrastructure

Hardware documentation should include validation using commands such as:

```bash
rpicam-hello
```

Camera Module 3 autofocus should be handled by the camera implementation rather than by calling code.

---

# Dependency Management

Before adding a dependency, consider:

1. Is it actively maintained?
2. Is it compatible with Raspberry Pi ARM64?
3. Does it substantially reduce complexity?
4. Can the same behavior be implemented simply without it?
5. Does it introduce system-level dependencies?
6. How will it be installed automatically?

Do not add libraries for trivial functionality.

All new required dependencies must be reflected in installation automation and documentation.

---

# Development Workflow

Prefer incremental development.

For each meaningful feature:

1. Design
2. Document architectural intent
3. Implement
4. Add tests
5. Perform hardware validation if applicable
6. Review
7. Refactor if needed
8. Update documentation

Avoid implementing several large subsystems simultaneously.

Prefer small, complete milestones.

---

# Git Practices

Keep commits focused.

Prefer commits describing one coherent change.

Examples:

```text
Add camera abstraction and PiCamera implementation

Add hardware validation script for Camera Module 3

Configure pytest and ruff

Add Raspberry Pi installation script
```

Avoid large commits that mix unrelated refactoring, documentation, and features unless necessary.

Do not commit:

* virtual environments
* generated caches
* local IDE configuration
* secrets
* credentials
* API keys
* SSH keys
* captured user photos
* machine-specific runtime data

---

# Security

Never commit secrets.

This includes:

* private SSH keys
* API keys
* tokens
* passwords
* private certificates

Use environment variables or appropriate configuration mechanisms when secrets become necessary.

Captured photographs should be treated as user data.

Do not include real user photographs in tests or the repository.

Use synthetic fixtures or intentionally provided sample images.

---

# Performance

PiPrints runs on Raspberry Pi hardware, so performance matters.

However, do not prematurely optimize.

Prioritize:

1. correct architecture
2. correctness
3. readability
4. profiling
5. targeted optimization

Pay particular attention to:

* large image copies
* unnecessary image conversions
* blocking work on the UI thread
* camera buffers
* memory usage
* synchronous printer operations
* repeated filesystem I/O

Do not optimize based solely on assumptions.

Measure when performance becomes meaningful.

---

# Concurrency

Do not block the PySide6 UI thread with long-running work.

Operations likely to require asynchronous or worker execution include:

* image processing
* printing
* long filesystem operations
* certain camera operations

Prefer Qt-compatible concurrency mechanisms when interaction with the UI is involved.

Do not introduce concurrency without a clear need.

Shared mutable state should be minimized.

---

# Open-Source Quality

Assume PiPrints may eventually have outside contributors.

Code should be understandable to someone who did not design the system.

When modifying architecture:

* preserve clear boundaries
* explain non-obvious decisions
* update documentation
* avoid unnecessary breaking changes
* keep public interfaces small

A contributor should be able to understand where new functionality belongs by inspecting the project structure.

---

# Avoid Overengineering

Professional architecture does not mean maximizing abstraction.

Do not create:

* factories when only one object is constructed and variability is unlikely
* repositories when simple filesystem access is sufficient
* service classes that merely forward every method to another class
* interfaces containing only one method solely for appearance
* deep inheritance structures
* generic frameworks inside PiPrints

Add abstractions when there is a meaningful boundary, testing benefit, hardware boundary, or expected variation.

Prefer the simplest architecture that preserves long-term maintainability.

---

# Agent Behavior

When working in this repository:

1. Inspect existing code before proposing changes.
2. Preserve established architecture unless there is a strong reason to change it.
3. Explain significant architectural changes.
4. Keep changes focused on the current task.
5. Do not refactor unrelated code without justification.
6. Add or update tests when behavior changes.
7. Update documentation when user-facing behavior, installation, hardware requirements, or architecture changes.
8. Consider Raspberry Pi ARM64 compatibility before adding dependencies.
9. Do not assume hardware is available in automated tests.
10. Prefer PiPrints-owned abstractions at subsystem boundaries.
11. Avoid silently introducing new architectural patterns.
12. Keep implementations easy for future contributors to understand.

If a requested implementation conflicts with these principles, prefer the maintainable architecture and explain the tradeoff.

---

# Current Project Priorities

The initial development sequence is:

1. Establish project packaging and development tooling.
2. Establish automated Raspberry Pi installation.
3. Configure testing and linting.
4. Implement the camera abstraction.
5. Implement the Raspberry Pi Camera Module integration.
6. Add hardware camera validation.
7. Build the initial PySide6 application shell.
8. Integrate live camera preview.
9. Build the booth workflow incrementally.
10. Add image processing, storage, printing, themes, and additional hardware integrations as separate milestones.

Do not skip architectural foundations to prematurely implement the complete photo booth workflow.

The goal is not merely to make PiPrints work.

The goal is to make PiPrints understandable, maintainable, extensible, testable, and worthy of long-term open-source development.

