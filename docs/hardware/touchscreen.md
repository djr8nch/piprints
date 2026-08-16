# 7-inch touchscreen validation

PiPrints is designed for an 800x480 landscape capacitive touchscreen connected
to a Raspberry Pi 4. Automated tests check the presentation at this viewport,
but they cannot validate physical ergonomics or display hardware.

After the display is installed, launch PiPrints at its native 800x480
resolution and complete this checklist:

1. Confirm tap accuracy for every primary control, including the Back controls
   and the review actions near the bottom of the display.
2. Confirm controls are comfortable to tap with a finger, do not trigger from
   adjacent touches, and reject accidental rapid double taps.
3. Read Home, capture progress, countdown, processing, review status, and
   errors from normal booth standing distance; adjust display brightness as
   needed.
4. Verify the review photo remains visible above its actions and is not
   distorted.
5. Check edge-touch usability, especially the lower-left Back control.
6. Validate DSI/display operation, required orientation, and native 800x480
   output with Raspberry Pi OS.
7. Validate the separately configured kiosk behavior: full-screen launch,
   hidden cursor, and appropriate screen blanking policy.

Kiosk startup, cursor hiding, screen blanking, and DSI troubleshooting are
Hardware/Deployment responsibilities; this checklist does not configure them.
