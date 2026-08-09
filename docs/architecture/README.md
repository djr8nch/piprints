# Architecture

## Basic booth capture workflow

Booth Milestone 1 keeps the workflow and presentation boundaries explicit:

```text
PySide6 UI
    ↓ user intent and rendered state
BoothController
    ↓ PiPrints-owned Camera contract
PiCamera
    ↓
Picamera2
```

`BoothController` owns the small `IDLE → COUNTDOWN → CAPTURING → REVIEW`
state flow and the runtime capture path. It has no Qt, widget, or camera-driver
knowledge, allowing deterministic tests with a fake `Camera`.

The UI owns the three-second visual countdown through a Qt timer. It stops the
preview frame worker before a short-lived Qt worker calls the controller's
blocking capture operation. `PiCamera` switches to a full-resolution still
configuration for that capture, then restores its preview configuration before
review or retake resumes live frames.
