# Booth lifecycle

## Purpose

The booth workflow coordinates one photo booth interaction without coupling
application logic to PySide6, Picamera2, filesystem implementations, or
printer hardware. `BoothController` owns lifecycle transitions and one active
`BoothSession`.

## States and transition ownership

`BoothState` represents the controller's current lifecycle state. The
controller validates every transition in one explicit transition map; UI code
only requests controller operations and renders the resulting events.

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PREPARING: begin session
    PREPARING --> COUNTDOWN: start countdown
    COUNTDOWN --> CAPTURING: countdown complete
    CAPTURING --> PREPARING: more photos required
    CAPTURING --> PROCESSING: required photos captured
    PROCESSING --> REVIEW: layout ready
    REVIEW --> COMPLETE: complete session
    COMPLETE --> IDLE: finish session
    REVIEW --> IDLE: retake
    COUNTDOWN --> ERROR
    CAPTURING --> ERROR
    PROCESSING --> ERROR
    ERROR --> IDLE: reset session
```

The controller supports layouts with any positive `required_photos` value.
After a non-final capture it returns to `PREPARING`, preserving the active
session, so multi-photo layouts do not require layout-specific workflow
branches.

## Session and component responsibilities

```mermaid
flowchart LR
    Controller["BoothController"] --> Session["BoothSession"]
    Controller --> Countdown["Countdown"]
    Controller --> Camera["Camera"]
    Controller --> Loader["PhotoLoader"]
    Controller --> Pipeline["PhotoPipeline"]
    Controller --> Layout["Layout"]
    Controller --> Storage["PhotoStorage"]
    Controller --> Printer["Optional Printer"]
    Camera --> CapturePath["capture path"]
    Loader --> Photo["Photo"]
    Pipeline --> Session
    Session --> Layout
    Layout --> Session
```

`BoothSession` owns its ID, ordered processed capture photos, progress, and the
final `Photo`. The controller orchestrates collaborators but does not decode
images, transform pixels, compose layouts, control camera hardware, or wait on
time itself. At review completion, it saves the final photo through
`PhotoStorage` and optionally submits that same prepared photo through
`Printer`. `Countdown` owns timing; camera implementations own hardware; the
imaging collaborators own image work.

## Event flow

```mermaid
flowchart LR
    Controller["BoothController"] -->|"BoothEvent"| Listener["BoothEventListener"]
    Listener --> Ui["Qt event bridge"]
    Listener --> Diagnostics["Future diagnostics"]
```

The controller emits state-change events, session starts/completion, countdown
ticks, captured photos, review readiness, output saving, print success/failure,
and errors. `OUTPUT_SAVED` includes the storage path; `PRINT_COMPLETED` includes
the `PrintResult`; `PRINT_FAILED` includes a diagnostic message. Listeners are
registered per controller, never globally. Listener exceptions are logged and
ignored so observation cannot corrupt the workflow.

## Failure and reset

Camera, load, pipeline, layout, and countdown failures transition the
controller to `ERROR`, publish an `ERROR` event, and clear the active session.
Capture and processing failures preserve the original exception as the cause of
the raised `BoothCaptureError`. `reset_session()` is the explicit `ERROR →
IDLE` recovery operation. A successful reviewed session follows
`complete_session()` then `finish_session()`; `retake()` discards a reviewed
session directly to `IDLE`. A storage failure leaves the session in `REVIEW`
and raises `BoothStorageError`. A printer failure occurs only after successful
storage, publishes `PRINT_FAILED`, leaves the session in `REVIEW`, and raises
`BoothPrintError`; callers may retry printing or retake without losing the
digital output. No `PRINTING` state is used because print submission is
synchronous and has no current user-visible progress phase.
