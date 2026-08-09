# ADR 0001: Raspberry Pi-first architecture

## Status

Accepted

## Context

PiPrints controls a Raspberry Pi camera through Raspberry Pi OS camera
infrastructure. The current setup script installs Raspberry Pi OS packages and
the implemented hardware adapter targets Picamera2/libcamera.

## Decision

PiPrints targets Raspberry Pi hardware and Raspberry Pi OS directly. It does
not add cross-platform hardware abstractions solely to support desktop
operating systems.

## Consequences

Hardware behavior can use the supported Raspberry Pi camera stack directly and
remain focused. Non-Raspberry Pi machines can still be used as development
clients, for example through Remote SSH, but they are not the reference runtime
or a substitute for hardware validation.
