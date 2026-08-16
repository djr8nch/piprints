# Architecture overview

## Purpose

PiPrints is a Raspberry Pi-first photo booth platform. Its current design
prioritizes high cohesion, low coupling, dependency inversion, composition over
inheritance, testability, and hardware isolation. The codebase grows in small
milestones so new hardware and workflow capabilities can be added without
turning the application into a hardware-specific UI.

## Current implementation

The alpha implements application startup, a multi-photo booth workflow,
Raspberry Pi camera control, composable imaging, digital filesystem persistence,
and a hardware-independent printer contract. `app.py` starts
the application and owns process-level camera cleanup. `bootstrap.py` is the
composition root: it creates `PiCamera`, `PhotoPipeline`, `FourPhotoLayout`,
`FilesystemPhotoStorage`, `BoothController`, and `MainWindow`, then injects
the dependencies they need.

`BoothController` owns lifecycle transitions; `BoothState` represents the
current lifecycle state. The controller also owns one active `BoothSession`,
created with the selected layout's `required_photos`. It adds each processed
capture, composes only after the session is complete, and coordinates imaging
collaborators without decoding or transforming pixels. On session completion,
it asks an injected `PhotoStorage` to persist the final photo and, when
configured, submits that same photo to an injected `Printer`; it never builds
output paths or uses hardware-specific printer APIs itself.

`BoothSession` is the booth-layer record for one interaction's identity,
layout-derived capture requirement, and image artifacts. It holds ordered
captured `Photo` values and, once composed, one final `Photo`; it has no
hardware, UI, layout, or persistence behavior.
`PiCamera` adapts Picamera2 and libcamera behind that contract. It configures
continuous autofocus for Camera Module 3, supplies standard `PreviewFrame`
values for live preview, and switches to a still configuration for capture.

The UI uses PySide6. The IDLE home screen leads to a layout-selection screen,
which renders only `LayoutCatalog` descriptors and asks `BoothController` to
begin a session with the selected identifier. This keeps concrete composition
strategies in the application/bootstrap boundary rather than the UI.
After choosing a layout, the user chooses a theme from `ThemeCatalog` metadata.
Only currently usable options are exposed; the selected identifier is stored in
`BoothSession` when the controller starts the session. `ThemeSelectionScreen`
may display a supplied preview file, but it does not compose images, apply
watermarks or overlays, choose fonts, or define colours. Those rendering and
branding concerns remain owned by the future Themes & Branding milestone.
`BoothScreen` renders the countdown, review, and retake controls.
`CameraPreviewWidget` obtains `PreviewFrame` values on a worker thread,
retains only the latest frame, and paints it from a Qt timer. The still
capture is also performed by a short-lived Qt worker so the UI thread remains
responsive.

```mermaid
flowchart TD
    Bootstrap["bootstrap.py<br/>composition root"]
    App["app.py"] --> Bootstrap
    Bootstrap --> CameraImpl["PiCamera"]
    Bootstrap --> Pipeline["PhotoPipeline"]
    Bootstrap --> Layout["FourPhotoLayout"]
    Bootstrap --> Storage["FilesystemPhotoStorage"]
    Bootstrap --> Booth["BoothController"]
    Bootstrap --> Window["MainWindow / BoothScreen"]

    Window -->|user intent| Booth
    Booth -->|still capture| CameraContract["Camera contract"]
    Booth -->|capture path| Loader["PhotoLoader"]
    Loader --> Photo["Photo"]
    Booth --> BoothSession["BoothSession"]
    Booth -->|one photo| Pipeline
    Pipeline -->|processed photo| BoothSession
    BoothSession -->|complete sequence| Layout
    BoothSession --> CapturedPhotos["Photo, Photo, ..."]
    Layout -->|final photo| BoothSession
    Booth -->|final photo + session ID| Storage
    Booth -->|final photo, optional| Printer["Printer contract"]
    BoothSession -->|final photo| Window
    Window -->|preview frames| CameraContract
    CameraImpl --> CameraContract
    CameraImpl --> Driver["Picamera2 / libcamera"]
```

## Printing boundary

`piprints.printing.Printer` is the hardware-independent contract for physical
output. It receives a fully prepared final `Photo` and returns a `PrintResult`
when that photo has been accepted for printing. Printer adapters may raise
`PrintError` when submission fails. The contract has no serial, raster, or
printer-model details, and it does not choose layouts or transform pixels.

At `complete_session()`, the controller saves the reviewed final photo first,
then submits it to an optional `Printer`, and only then enters `COMPLETE`.
Digital-only booths omit the printer dependency. A print failure leaves the
session in `REVIEW`, retaining the saved output so it can be retried or
retaken without recapturing. There is no `PRINTING` state because the current
contract is synchronous and provides no user-visible progress phase.

Application orchestration depends on `Printer`, while a hardware-specific
adapter implements that contract:

```mermaid
flowchart BT
    Booth["Booth / application"] --> Printer["Printer contract"]
    Adapter["Hardware-specific printer adapter"] --> Printer
```

`piprints.printing.thermal.ThermalRasterEncoder` is a pure printer-preparation
component, not a transport adapter. It converts an already composed `Photo` to
row-major monochrome bytes: black dots are set bits, leftmost dots occupy the
most-significant bit, and each row is padded with white bits to a whole byte.
An optional configured maximum dot width rejects oversized photos rather than
silently resizing, cropping, or changing the booth layout. Any printer-width
resizing will be a separate, explicit preparation decision before encoding.
Protocol framing and hardware transport remain future adapter responsibilities.

`piprints.printing.thermal.PySerialTransport` is the infrastructure boundary
for that future adapter. It opens configured raw serial connections, writes all
bytes or raises `SerialTransportError`, and closes connections explicitly or
through a context manager. Its `SerialTransportSettings` requires an injected
device path and baud rate, with an optional timeout (one second by default);
it does not assume a particular `/dev` device or printer model.

`PrimuzThermalPrinter` composes the raster encoder and serial transport behind
the generic `Printer` contract. It is intentionally pre-hardware-validation:
the sole raster framing command is an explicitly documented ESC/POS assumption,
not a claim of verified PRIMUZ compatibility. No printer is created by default
at bootstrap, so digital-only runtime startup remains independent of hardware.

The UI depends directly on the PiPrints-owned camera contract only for preview
frames. Workflow commands travel through `BoothController`; neither path gives
the UI a Picamera2 or libcamera object. A focused UI presentation adapter turns
the final imaging `Photo` into a Qt pixmap; it does not perform image
processing.

## Booth event boundary

`BoothController` publishes immutable `BoothEvent` values to explicitly
registered `BoothEventListener` instances. Events currently cover session
starts and completion, state changes, countdown ticks, captured photos, review
readiness, and errors. The controller catches and logs listener exceptions so
an optional presentation or diagnostics listener cannot corrupt the workflow.

```mermaid
flowchart LR
    Controller["BoothController"] -->|"BoothEvent"| Bridge["QtEventBridge"]
    Bridge -->|"Qt Signal"| Ui["PySide6 UI"]
    Controller -->|"BoothEvent"| Diagnostics["Future diagnostics listener"]
```

This Observer boundary lets the UI render application occurrences without
introducing a PySide6 dependency into booth logic. `QtEventBridge` is an
Adapter in `piprints.ui`: bootstrap registers it with the controller and passes
the same instance to the window. It translates the state-change, countdown,
review-ready, and error events currently needed by the UI into Qt signals.
Qt queues slots to the receiver's thread when worker-originated events are
emitted, so the bridge never causes widget updates from a booth worker. It does
not decide state transitions, timing, or any hardware, imaging, storage, or
printing behavior.

## Imaging pipeline and layouts

The imaging subsystem separates two distinct operations:

- `PhotoPipeline` applies an ordered sequence of `PhotoOperation` objects to
  exactly one in-memory `Photo`. The current `ResizeOperation` uses Pillow's
  high-quality Lanczos resampling. Pillow is a maintained dependency with
  Raspberry Pi ARM64-compatible Linux packages and provides the small,
  well-supported image API needed for this milestone.
- `CenterCropAspectRatioStrategy` makes a pixel-independent framing decision:
  given source dimensions and an `AspectRatio`, it returns the largest centered
  `CropBox` that matches the ratio using whole integer ratio units. If a source
  has an odd remainder, the extra pixel stays on the right or bottom edge.
  `CropOperation` applies that explicit box, then `ResizeOperation` scales the
  result. This order discards unwanted pixels before scaling and is assembled
  by callers as normal pipeline operations; `PhotoPipeline` has no framing
  knowledge.
- A `Layout` is a Strategy that receives processed photos and returns one final
  `Photo`. `SinglePhotoLayout` returns its one input unchanged.
  `FourPhotoLayout` arranges four photos in a 2×2 grid, and
  `ClassicPhotoStripLayout` stacks four photos vertically. Both own their
  canvas geometry and use the same imaging crop/resize primitives to fill each
  cell. They have no camera or Qt dependency.

`PhotoLoader`, also owned by `imaging`, is the narrow boundary between the
current path-based camera contract and the in-memory `Photo` model. It decodes
and copies captures to RGB before processing. `Photo` itself only wraps the
in-memory Pillow image; it has no capture-path or persistence responsibility.

Every layout declares `required_photos`. `BoothController` passes that value to
`BoothSession`, so selecting a layout changes the session target without
layout-specific workflow branches. The session exposes an immutable photo
snapshot, count, remaining count, and completion state; it does not own camera
access, timing, layout composition, or persistence.

The UI uses the final `Photo` from the selected layout for review and Qt's
normal pixmap scaling for presentation. It does not calculate a separate
preview layout or manipulate Pillow images. This makes the preview an exact
presentation of the final composition and avoids composition work until a
session completes.

## Current capture workflow

```mermaid
flowchart LR
    Idle["Idle: Home"] -->|Start| LayoutSelection["Layout Selection"]
    LayoutSelection -->|Choose layout| Preparing["Preparing"]
    Preparing -->|Take Photo| Countdown["Countdown: 3, 2, 1"]
    Countdown --> Capturing["Capturing: still image"]
    Capturing -->|session incomplete| Preparing
    Capturing -->|session complete| Processing
    Processing --> Review["Review final layout"]
    Review -->|Retake| Idle
    Review -->|Complete session| Complete
    Complete -->|Finish session| Idle
    Capturing -->|camera error| Error
    Error -->|Reset session| Idle
```

`Countdown` is a framework-independent booth service. It yields configured
countdown ticks through an injected delay callable, so unit tests can use a
no-op delay while the runtime uses normal wall-clock sleep. `BoothController`
owns countdown execution and transitions from `COUNTDOWN` to `CAPTURING` once
the ticks complete. `BoothScreen` runs that blocking application work on a Qt
worker and renders its ticks; it does not own timing or decide the lifecycle
transition. The screen renders `Photo n of N` from `BoothSession` instead of
keeping a second progress counter.

The preview worker stops before the still capture begins. Picamera2 restores
the preview configuration after the still capture, and the preview worker is
started again when the user selects **Retake**. Captures currently go to the
runtime `captures/` directory; this is not a storage or session subsystem.

## Booth lifecycle states

`BoothState` is the booth layer's framework-independent lifecycle vocabulary.
It is a small enum, not a class-per-state State pattern.

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PREPARING
    PREPARING --> COUNTDOWN
    COUNTDOWN --> CAPTURING
    CAPTURING --> PROCESSING
    PROCESSING --> REVIEW
    REVIEW --> COMPLETE
    COMPLETE --> IDLE
    COUNTDOWN --> ERROR
    CAPTURING --> ERROR
    PROCESSING --> ERROR
    ERROR --> IDLE
```

`BoothController` owns the allowed lifecycle transitions, while `BoothState`
represents the current lifecycle state. This increment implements session
creation (`IDLE → PREPARING`), capture and processing transitions, review,
completion/reset, failure cleanup, and framework-independent countdown
execution. UI observation remains separate. The enum has no dependency on Qt,
hardware, imaging, printing, or persistence.

The complete transition rules, component boundaries, events, and recovery
behavior are documented in the [booth lifecycle](booth-lifecycle.md).

## Package responsibilities

| Package | Current responsibility |
| --- | --- |
| `booth` | Implemented: lifecycle transitions, session artifacts and progress, countdown progression, camera coordination, final-session composition, and output orchestration through `PhotoStorage` and optional `Printer` contracts. |
| `camera` | Implemented: `Camera` contract, `PreviewFrame`, domain errors, and Picamera2 adapter. |
| `config` | Placeholder for future runtime configuration. |
| `imaging` | Implemented: in-memory `Photo`, path loader, per-photo pipeline, deterministic framing and crop/resize operations, layout contracts, and single/grid/strip layouts. It is independent of UI, camera hardware, storage, and printing. |
| `input` | Placeholder for future user and hardware input integration. |
| `printing` | Implemented: hardware-independent `Printer` contract, successful-submission `PrintResult`, and `PrintError`. Hardware-specific adapters are future work. |
| `storage` | Implemented: `PhotoStorage` contract and filesystem persistence for completed final photos. The default runtime location is `photos/YYYY-MM-DD/` under the working directory. |
| `themes` | Placeholder for future UI theming. |
| `ui` | Implemented: PySide6 preview, booth screen, and top-level window. |
| `utils` | Placeholder; no shared utility behavior is implemented yet. |

## Dependency rules

- UI code must not import Picamera2 or libcamera.
- Picamera2/libcamera behavior belongs in `piprints.camera`.
- Booth logic must not know PySide6 widget details.
- `bootstrap.py` may depend on concrete implementations because it is the
  composition root.
- Business rules should use PiPrints-owned abstractions where practical.
- Default CI must not require Raspberry Pi hardware.

Allowed:

```text
BoothController → Camera
BoothController → BoothSession + PhotoLoader + PhotoPipeline + Layout
BoothController → PhotoStorage
BoothController → optional Printer
CameraPreviewWidget → Camera / PreviewFrame
bootstrap.py → PiCamera + BoothController + MainWindow
```

Discouraged:

```text
BoothScreen → Picamera2
BoothController → QWidget
Camera adapter → BoothScreen
PhotoPipeline → Layout
Printer adapter → BoothController
```

## Test boundaries

`tests/unit/` covers hardware-independent package, booth, and camera-adapter
behavior using fakes. `tests/integration/` covers PySide6 widgets and bootstrap
wiring with Qt's offscreen platform. Physical camera checks remain manual and
are excluded from standard CI.

## Future evolution

Hardware-specific printing, themes, input hardware, sharing, and video are not
implemented. Runtime framing targets and output
dimensions will be introduced through configuration rather than hard-coded in
the imaging pipeline. When those milestones begin, they should be added at the
package boundaries above rather than folded into the current booth or UI
classes.

## Design decisions

The reasoning behind established architectural choices is recorded in the
[architecture decision records](decisions/README.md).
