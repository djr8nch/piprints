# Raspberry Pi Camera

PiPrints supports Raspberry Pi Camera Modules through Picamera2. Camera Module
3 is the primary target and is configured for continuous autofocus when
started. Camera Milestone 2 displays a live preview in the PiPrints window.

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

## Validate the booth capture workflow

Launch PiPrints from the repository root:

```bash
./scripts/run.sh
```

Verify all of the following manually on the Raspberry Pi:

1. The PiPrints window displays a smooth live camera image.
2. Moving the subject changes focus automatically on Camera Module 3.
3. Select **Take Photo** and verify a visible 3, 2, 1 countdown.
4. Verify the captured image appears in review after the countdown.
5. Select **Retake** and verify that live preview resumes.
6. Repeat the capture and retake flow multiple times.
7. Resize the window during preview and review without a crash.
8. Close PiPrints, then run `./scripts/run.sh` again to confirm the camera was
   released.

This validation requires physical hardware and a display, so it must not be
added to the standard pytest suite.
