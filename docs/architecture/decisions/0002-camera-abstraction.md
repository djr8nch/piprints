# ADR 0002: Camera abstraction around Picamera2

## Status

Accepted

## Context

The application needs to start and stop a camera, capture still images, and
deliver preview frames. Picamera2 and libcamera are Raspberry Pi implementation
details that should not spread into booth or UI code.

## Decision

Higher-level code depends on the PiPrints-owned `Camera` contract and
`PreviewFrame` type. `PiCamera` adapts Picamera2 and owns autofocus, stream
configuration, still capture, and translation of hardware failures into
PiPrints exceptions.

## Consequences

The booth controller and UI can be tested with simple fakes and do not import
Picamera2 or libcamera. Adding another camera implementation later has a
defined boundary, while the current interface remains limited to operations
PiPrints actually needs.
