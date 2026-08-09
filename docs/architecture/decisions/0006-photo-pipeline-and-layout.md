# ADR 0006: Separate per-photo processing from layout composition

## Status

Accepted

## Context

PiPrints needs to transform individual captures and eventually combine multiple
processed captures into outputs such as photo strips. Combining both concerns
in one processor would make operations depend on capture count and make layouts
responsible for individual image transformations.

## Decision

Use `PhotoPipeline` to apply ordered `PhotoOperation` objects to exactly one
in-memory `Photo`. Use the `Layout` Strategy interface to compose processed
photos into one final `Photo`. Each layout declares `required_photos`, which
will let the booth workflow derive its future capture count from the selected
layout.

Pillow backs the intentionally small `Photo` model and the initial resize
operation. `PhotoLoader` keeps the temporary path-to-photo conversion within
the imaging package, while a UI presentation adapter isolates Photo-to-Qt
conversion.

## Consequences

Image operations remain reusable and independently testable. Layouts can be
added without changing individual operations, and future multi-photo booth
flows can rely on the layout's declared requirement. The imaging package stays
independent of camera hardware, Qt widgets, printing, and storage.
