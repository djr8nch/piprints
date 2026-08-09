# Development

## Run the basic booth workflow

On a Raspberry Pi with PiPrints installed, start the current application with:

```bash
./scripts/run.sh
```

The application creates the hardware camera and booth controller in
`bootstrap.py`. The PySide6 UI receives the controller and PiPrints camera
abstraction, never Picamera2. See the [camera hardware guide](../hardware/camera.md)
for physical validation and troubleshooting prerequisites.
