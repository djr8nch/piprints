# Development

## Run the live camera preview

On a Raspberry Pi with PiPrints installed, start the current application with:

```bash
./scripts/run.sh
```

The application creates the hardware camera in `bootstrap.py`, starts it at
application startup, and passes only the PiPrints camera abstraction to the
PySide6 preview widget. See the [camera hardware guide](../hardware/camera.md)
for physical validation and troubleshooting prerequisites.
