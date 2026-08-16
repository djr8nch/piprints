# Testing

PiPrints separates tests by architectural boundary so failures identify whether
core behavior or cross-subsystem UI behavior needs attention.

## Unit tests

Unit tests live under `tests/unit/`. They are fast, deterministic, and do not
require real Raspberry Pi hardware. They cover package metadata, booth workflow
rules, and the PiCamera adapter through a local fake of the external Picamera2
dependency.

Unit tests should avoid Qt unless the unit under test specifically needs it.
They should use PiPrints-owned interfaces and simple fakes rather than physical
devices.

## Integration tests

Integration tests live under `tests/integration/`. They may cross subsystem
boundaries, use PySide6, and exercise bootstrap or main-window wiring. CI runs
them headlessly with `QT_QPA_PLATFORM=offscreen` and the Linux libraries needed
by Qt.

## Test fakes

Reusable fakes live under `tests/fakes/`. `FakeCamera` implements the
PiPrints-owned `Camera` contract and records calls without hardware access.
This keeps booth and application tests explicit and small without extensive
mocking.

The Picamera2 adapter tests intentionally keep `FakePicamera2` local to their
test module: it represents an external dependency rather than a reusable
PiPrints abstraction.

## Hardware validation

Raspberry Pi camera validation is currently manual and script-driven. It is not
part of normal GitHub-hosted CI because it needs a physical camera and display.
See the [camera guide](../hardware/camera.md) for validation steps.

## Commands

From an activated development environment, run:

```bash
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest
python -m ruff check .
```

GitHub Actions runs the same boundaries in separate jobs: **Lint**, **Unit
tests**, and **Integration tests**. Default CI must never require Raspberry Pi
hardware.

## Imaging benchmarks

Run the standalone imaging benchmark on a Raspberry Pi reference device with:

```bash
PYTHONPATH=src python scripts/benchmark_imaging.py
```

Use `--repetitions` to collect more samples, for example
`PYTHONPATH=src python scripts/benchmark_imaging.py --repetitions 10`. The
script generates 1920x1080 and 4608x2592 RGB images in memory and reports mean
elapsed time for framing calculation, crop, resize, the crop-and-resize
pipeline, and the current single-photo imaging pipeline.

These figures establish historical Raspberry Pi baselines and help identify
regressions; they are not CI pass/fail thresholds. GitHub-hosted x86 timing is
not representative of PiPrints runtime performance.
