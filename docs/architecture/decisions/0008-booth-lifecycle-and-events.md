# ADR 0008: BoothController owns lifecycle orchestration and events

## Status

Accepted

## Context

PiPrints needs an end-to-end photo booth workflow that coordinates camera
capture, countdown timing, image processing, composition, review, completion,
and recovery. Those responsibilities must remain independently testable and
must not require a PySide6 dependency in the application layer.

## Decision

`BoothController` owns one active `BoothSession` and validates explicit
`BoothState` transitions. It orchestrates the PiPrints-owned `Camera`,
`Countdown`, `PhotoLoader`, `PhotoPipeline`, and `Layout` contracts without
implementing their low-level behavior.

The controller publishes immutable `BoothEvent` values to explicitly registered
`BoothEventListener` instances. Listener failures are logged and isolated from
the workflow. Failures leave the controller in `ERROR` until an explicit
`reset_session()` returns it to `IDLE`.

## Consequences

Presentation code can render events through a narrow adapter while booth logic
remains independent of Qt. Multi-photo layouts use the layout's
`required_photos` value without controller branches. The controller remains a
small orchestration boundary; new hardware, image, or presentation behavior
belongs behind its existing collaborators rather than inside it.
