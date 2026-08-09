# ADR 0003: PySide6 for the UI

## Status

Accepted

## Context

PiPrints needs a responsive graphical interface for live camera preview and
the initial booth flow. The project metadata declares PySide6 as its UI
dependency, and the current interface uses Qt widgets, timers, signals, and
worker threads.

## Decision

Use PySide6 for the PiPrints user interface. UI classes render application
state and forward user intent; they do not contain Picamera2/libcamera behavior
or booth workflow rules.

## Consequences

Preview and still-capture work can use Qt-compatible workers and timers without
blocking the UI thread. UI integration tests require Qt and run headlessly in
CI, while workflow and camera adapter rules remain testable outside the UI.
