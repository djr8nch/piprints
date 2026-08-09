# ADR 0004: Lightweight dependency injection through bootstrap.py

## Status

Accepted

## Context

The application needs concrete `PiCamera`, `BoothController`, and PySide6
window instances, while the booth and UI should receive only the dependencies
they need. The current codebase is small and does not need a dependency
injection framework.

## Decision

Use `bootstrap.py` as the composition root. It creates the concrete camera,
booth controller, application, and main window, then injects dependencies via
constructors.

## Consequences

Concrete implementation knowledge is localized at startup, and tests can
inject fakes into booth and UI composition. The project avoids global service
lookups and framework configuration while its dependency graph remains small.
