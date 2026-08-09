# Development setup

## Supported environment

PiPrints is developed and run primarily on a 64-bit Raspberry Pi OS system.
The reference runtime is a Raspberry Pi with a supported camera connected; the
project requires Python 3.11 or newer as declared in `pyproject.toml`.

Another computer can be used as a development client, but it is not the target
runtime. For example, VS Code Remote SSH can edit and run the project on the
Raspberry Pi from macOS, Linux, or Windows while preserving the Raspberry Pi
camera environment.

## Install on Raspberry Pi OS

Clone the repository, then run the setup script from the project root:

```bash
git clone <repository-url>
cd piprints
./scripts/install.sh
```

The script updates apt metadata, installs `python3`, `python3-venv`, and
`python3-picamera2`, creates `.venv` when it does not already exist, and
installs PiPrints in editable mode with its development dependencies.

It uses `sudo` for the Raspberry Pi OS packages. Re-running the script keeps an
existing virtual environment and reinstalls the editable project.

## Why the virtual environment includes system packages

The setup script creates `.venv` with `--system-site-packages`. Picamera2 and
its libcamera integration are provided by Raspberry Pi OS through apt, not as a
normal project pip dependency. Making system packages visible inside `.venv`
allows the editable PiPrints installation to import the OS-managed Picamera2
package while preserving an isolated place for development tools such as pytest
and Ruff.

Activate the environment manually when needed:

```bash
source .venv/bin/activate
```

To install or refresh the editable development dependencies without rerunning
the system setup:

```bash
python -m pip install -e ".[dev]"
```

## Run PiPrints

Use the repository script so the project runs with `.venv`:

```bash
./scripts/run.sh
```

The current alpha opens the camera, displays a live preview, and supports the
basic countdown/capture/review/retake workflow. See the
[camera guide](../hardware/camera.md) before treating a failed application
launch as a PiPrints issue; first validate the operating-system camera stack.

## Optional VS Code Remote SSH workflow

1. Install the Remote - SSH extension on your development computer.
2. Connect to the Raspberry Pi over SSH and open the PiPrints repository.
3. Use the Raspberry Pi's `.venv/bin/python` interpreter in the remote window.
4. Run `./scripts/run.sh` from a terminal attached to the Raspberry Pi display
   environment, or use the local display/session appropriate to that device.

Remote SSH is optional. It does not make camera hardware available on the
client computer; PiPrints still executes on the Raspberry Pi.
