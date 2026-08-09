# Raspberry Pi Camera

PiPrints Camera Milestone 1 supports Raspberry Pi Camera Modules through
Picamera2. Camera Module 3 is the primary target and is configured for
continuous autofocus when started.

## Prerequisites

- A 64-bit Raspberry Pi OS installation with the modern libcamera stack.
- A supported Raspberry Pi Camera Module connected to the CSI camera port.
- PiPrints installed using `./scripts/install.sh`, which installs the
  `python3-picamera2` system package.

Do not use the deprecated legacy camera stack or legacy camera-enable setup
instructions.

## Validate the operating system camera stack

With the camera connected, verify that Raspberry Pi OS can detect and preview
it before running PiPrints:

```bash
rpicam-hello
```

Resolve hardware, cable orientation, and operating-system camera issues before
continuing if this command fails.

## Capture a test image

Activate the PiPrints virtual environment, then run:

```bash
.venv/bin/python scripts/camera_test.py
```

The script creates `captures/camera-test.jpg` relative to the repository root.
Provide another location with `--output` when needed:

```bash
.venv/bin/python scripts/camera_test.py --output captures/validation/image.jpg
```

The destination's parent directories are created automatically. This is a
manual hardware validation step and is intentionally excluded from pytest.
