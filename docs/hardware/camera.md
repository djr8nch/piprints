# Raspberry Pi Camera Module 3

## Supported behavior

The current PiPrints alpha targets Raspberry Pi Camera Module 3 on 64-bit
Raspberry Pi OS. It uses the modern Picamera2/libcamera stack to provide a live
preview, continuous autofocus, and still capture for the basic booth workflow.

Connect the camera ribbon cable to the Raspberry Pi CSI camera connector with
the board powered off. Confirm the connector and ribbon orientation against the
documentation for your Raspberry Pi model before powering it on.

PiPrints does not use the legacy camera stack. Do not follow old
`raspi-config` camera-enable instructions; current Raspberry Pi OS uses the
libcamera/rpicam stack instead.

## Prerequisites and operating-system validation

Install PiPrints with `./scripts/install.sh`. The script installs the
Raspberry Pi OS `python3-picamera2` package alongside the Python environment.

Before running PiPrints, validate that Raspberry Pi OS can open the camera:

```bash
rpicam-hello
```

Resolve detection or ribbon-cable problems at this level before debugging the
application.

## PiPrints validation

The single-capture script verifies the adapter and output path behavior:

```bash
.venv/bin/python scripts/camera_test.py
```

It writes `captures/camera-test.jpg` by default; `captures/` is runtime data
and is ignored by Git.

For the complete current booth flow, run:

```bash
./scripts/run.sh
```

Verify the following on the Raspberry Pi:

1. A live preview appears and remains responsive when the window is resized.
2. Camera Module 3 autofocus responds as the subject distance changes.
3. **Take Photo** shows a 3, 2, 1 countdown.
4. The captured still appears in review.
5. **Retake** returns to live preview.
6. Repeating the flow works without restarting PiPrints.
7. Closing PiPrints releases the camera; a second launch opens it again.

## Troubleshooting

### Camera is not detected

Run `rpicam-hello`. If it fails, shut down the Pi and recheck the CSI ribbon
connection and orientation. Verify that the system is using a supported,
non-legacy Raspberry Pi OS camera stack before investigating PiPrints logs.

### Image remains blurry

Camera Module 3 autofocus is configured to continuous mode when PiPrints
starts the camera. Give the camera a moment to focus after a large change in
subject distance. If it never focuses, validate the camera with `rpicam-hello`
and inspect the physical lens/camera installation.

### `.venv` cannot import Picamera2

Run `./scripts/install.sh` on the Raspberry Pi. It installs `python3-picamera2`
through apt and creates `.venv` with `--system-site-packages`, which exposes
that OS-managed package to the virtual environment. The setup script recreates
an incompatible existing `.venv` automatically. A conventional venv created
without that option may not see Picamera2.

### Camera is already in use

Close other camera applications, including `rpicam-hello`, then retry
`./scripts/run.sh`. Only one process can normally own the camera at a time.

### Camera remains unavailable after abnormal termination

Wait briefly for the operating system to release the device, then check for a
remaining PiPrints or camera process. End only the identified process before
launching PiPrints again. A normal PiPrints window close stops its workers and
then stops the camera during application shutdown.
